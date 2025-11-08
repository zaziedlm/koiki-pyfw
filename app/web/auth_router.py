from typing import Annotated, Optional

import structlog
from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from libkoiki.api.dependencies import (
    AuthServiceDep,
    DBSessionDep,
    LoginSecurityServiceDep,
    UserServiceDep,
)
from libkoiki.core.config import settings
from libkoiki.core.security import extract_device_info
from libkoiki.core.security_logger import security_logger
from libkoiki.core.security_metrics import security_metrics

from .templates import templates

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Web Auth"], include_in_schema=False)


def _safe_next_path(raw_next: Optional[str]) -> str:
    if raw_next and raw_next.startswith("/"):
        return raw_next
    return "/app/"


def _set_auth_cookies(response: RedirectResponse, access_token: str, refresh_token: str) -> None:
    access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    secure_cookie = not settings.DEBUG

    response.set_cookie(
        "access_token",
        access_token,
        max_age=access_max_age,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: RedirectResponse) -> None:
    for name in ("access_token", "refresh_token"):
        response.delete_cookie(name, path="/")


@router.get("/login", response_class=HTMLResponse)
async def login_form(
    request: Request,
    next: Optional[str] = None,
) -> HTMLResponse:
    context = {
        "request": request,
        "next": next or "/app/",
        "error": None,
    }
    return templates.TemplateResponse("auth/login.html", context)


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
    login_security_service: LoginSecurityServiceDep,
    db: DBSessionDep,
    email: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
    next: Annotated[Optional[str], Form()] = None,
) -> HTMLResponse:
    ip_address = request.client.host if request.client else "unknown"
    device_info = extract_device_info(request)
    redirect_target = _safe_next_path(next)

    logger.info("Web login attempt", email=email, ip_address=ip_address)

    allowed, reason, retry_after = await login_security_service.check_login_allowed(
        email=email,
        ip_address=ip_address,
        db=db,
    )

    if not allowed:
        logger.warning("Web login blocked", email=email, reason=reason, ip_address=ip_address)
        context = {
            "request": request,
            "next": redirect_target,
            "error": reason or "Login temporarily locked.",
        }
        return templates.TemplateResponse("auth/login.html", context, status_code=status.HTTP_429_TOO_MANY_REQUESTS)

    await login_security_service.apply_progressive_delay(email, ip_address, db)

    user = await user_service.authenticate_user(
        email=email,
        password=password,
        db=db,
    )

    if not user or not user.is_active:
        failure_reason = "inactive_user" if user and not user.is_active else "invalid_credentials"

        await login_security_service.record_login_attempt(
            email=email,
            ip_address=ip_address,
            is_successful=False,
            db=db,
            user_id=user.id if user else None,
            user_agent=device_info,
            failure_reason=failure_reason,
        )

        security_logger.log_authentication_attempt(
            email=email,
            ip_address=ip_address,
            user_agent=device_info,
            success=False,
            failure_reason=failure_reason,
        )
        security_metrics.record_authentication_attempt(
            success=False,
            email=email,
            ip_address=ip_address,
            failure_reason=failure_reason,
        )

        logger.warning("Web login failed", email=email, ip_address=ip_address, reason=failure_reason)
        context = {
            "request": request,
            "next": redirect_target,
            "error": "メールアドレスまたはパスワードが正しくありません。",
        }
        return templates.TemplateResponse("auth/login.html", context, status_code=status.HTTP_401_UNAUTHORIZED)

    await login_security_service.record_login_attempt(
        email=email,
        ip_address=ip_address,
        is_successful=True,
        db=db,
        user_id=user.id,
        user_agent=device_info,
    )

    security_logger.log_authentication_attempt(
        email=email,
        ip_address=ip_address,
        user_agent=device_info,
        success=True,
        user_id=user.id,
    )
    security_metrics.record_authentication_attempt(
        success=True,
        email=email,
        ip_address=ip_address,
    )

    access_token, refresh_token, _expires_in = await auth_service.create_token_pair(
        user=user,
        db=db,
        device_info=device_info,
    )

    logger.info("Web login successful", email=email, user_id=user.id, ip_address=ip_address)
    response = RedirectResponse(url=redirect_target, status_code=status.HTTP_303_SEE_OTHER)
    _set_auth_cookies(response, access_token, refresh_token)
    return response


@router.post("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse(url="/app/", status_code=status.HTTP_303_SEE_OTHER)
    _clear_auth_cookies(response)
    return response
