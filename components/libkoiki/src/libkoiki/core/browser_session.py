"""Browser-session helpers for the minimal React frontend.

The ordinary KOIKI APIs continue to use Bearer tokens.  This module provides a
narrow, explicit bridge for browser-only endpoints so access and refresh tokens
remain in HttpOnly cookies and are never returned to JavaScript.
"""

from __future__ import annotations

import hmac
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from libkoiki.core.config import settings
from libkoiki.core.security import get_user_from_token
from libkoiki.db.session import get_db
from libkoiki.models.user import UserModel
from libkoiki.repositories.user_repository import UserRepository

BROWSER_SESSION_HEADER = "x-koiki-browser-session"


def _cookie_secure() -> bool:
    """Always require Secure cookies when the application is in production."""
    return settings.BROWSER_COOKIE_SECURE or settings.APP_ENV == "production"


def _same_site() -> str:
    value = settings.BROWSER_COOKIE_SAMESITE.lower()
    return value if value in {"lax", "strict", "none"} else "lax"


def _cookie_options(*, max_age: int, http_only: bool) -> dict[str, object]:
    return {
        "httponly": http_only,
        "secure": _cookie_secure(),
        "samesite": _same_site(),
        "max_age": max_age,
        "path": "/",
    }


def generate_csrf_token() -> str:
    """Generate a cryptographically secure token for the double-submit cookie."""
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: str | None = None) -> str:
    """Set a JavaScript-readable CSRF cookie and return its value."""
    csrf_token = token or generate_csrf_token()
    response.set_cookie(
        key=settings.BROWSER_CSRF_COOKIE_NAME,
        value=csrf_token,
        **_cookie_options(max_age=settings.BROWSER_CSRF_TOKEN_MAX_AGE_SECONDS, http_only=False),
    )
    return csrf_token


def set_auth_cookies(response: Response, *, access_token: str, refresh_token: str) -> None:
    """Store token pair in HttpOnly cookies without exposing them in JSON."""
    response.set_cookie(
        key=settings.BROWSER_ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        **_cookie_options(
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            http_only=True,
        ),
    )
    response.set_cookie(
        key=settings.BROWSER_REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        **_cookie_options(
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            http_only=True,
        ),
    )


def clear_auth_cookies(response: Response) -> None:
    """Expire browser authentication cookies on logout or refresh failure."""
    for cookie_name in (
        settings.BROWSER_ACCESS_TOKEN_COOKIE_NAME,
        settings.BROWSER_REFRESH_TOKEN_COOKIE_NAME,
    ):
        response.delete_cookie(
            key=cookie_name,
            path="/",
            secure=_cookie_secure(),
            samesite=_same_site(),
        )


def has_valid_csrf_token(request: Request) -> bool:
    cookie_token = request.cookies.get(settings.BROWSER_CSRF_COOKIE_NAME)
    header_token = request.headers.get(settings.BROWSER_CSRF_HEADER_NAME)
    return bool(
        cookie_token
        and header_token
        and hmac.compare_digest(cookie_token, header_token)
    )


def require_browser_csrf(request: Request) -> None:
    """Reject unsafe browser-session calls without a matching CSRF token."""
    if not has_valid_csrf_token(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "CSRF token validation failed",
                "code": "CSRF_TOKEN_INVALID",
            },
        )


async def get_browser_active_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserModel:
    """Resolve an authenticated active user from the HttpOnly access-token cookie.

    This dependency is deliberately used only by ``/auth/browser`` endpoints.
    Bearer-token endpoints retain their existing OAuth2 dependency and contract.
    """
    access_token = request.cookies.get(settings.BROWSER_ACCESS_TOKEN_COOKIE_NAME)
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user_id = await get_user_from_token(access_token)
    user_repo = UserRepository()
    user_repo.set_session(db)
    current_user = await user_repo.get_user_with_roles_permissions(user_id)

    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    request.state.current_user = current_user
    request.state.auth_method = "browser_cookie"
    request.state.audit_user_id = current_user.id
    request.state.audit_user_email = current_user.email
    return current_user


BrowserActiveUserDep = Annotated[UserModel, Depends(get_browser_active_user)]


class BrowserSessionCSRFMiddleware(BaseHTTPMiddleware):
    """Enforce double-submit CSRF protection for browser-session mutations."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        browser_prefix = f"{settings.API_PREFIX}/auth/browser"
        unsafe_method = request.method in {"POST", "PUT", "PATCH", "DELETE"}

        if request.url.path.startswith(browser_prefix) and unsafe_method:
            if request.headers.get(BROWSER_SESSION_HEADER) != "1" or not has_valid_csrf_token(request):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "message": "CSRF token validation failed",
                        "code": "CSRF_TOKEN_INVALID",
                    },
                )

        return await call_next(request)