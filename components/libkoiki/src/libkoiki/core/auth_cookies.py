from datetime import timedelta
from typing import Any

from starlette.responses import Response

from libkoiki.core.config import settings


def access_cookie_max_age_seconds() -> int:
    return int(timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds())


def refresh_cookie_max_age_seconds() -> int:
    return int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())


def _cookie_options(max_age: int, *, http_only: bool) -> dict[str, Any]:
    options: dict[str, Any] = {
        "httponly": http_only,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "max_age": max_age,
        "path": settings.AUTH_COOKIE_PATH,
    }
    if settings.AUTH_COOKIE_DOMAIN:
        options["domain"] = settings.AUTH_COOKIE_DOMAIN
    return options


def set_access_token_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.AUTH_ACCESS_COOKIE_NAME,
        token,
        **_cookie_options(access_cookie_max_age_seconds(), http_only=True),
    )


def set_refresh_token_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        token,
        **_cookie_options(refresh_cookie_max_age_seconds(), http_only=True),
    )


def clear_auth_cookies(response: Response) -> None:
    for name in (
        settings.AUTH_ACCESS_COOKIE_NAME,
        settings.AUTH_REFRESH_COOKIE_NAME,
        settings.AUTH_CSRF_COOKIE_NAME,
    ):
        response.delete_cookie(
            name,
            path=settings.AUTH_COOKIE_PATH,
            domain=settings.AUTH_COOKIE_DOMAIN,
            secure=settings.AUTH_COOKIE_SECURE,
            httponly=name != settings.AUTH_CSRF_COOKIE_NAME,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )


def set_auth_cookies(response: Response, *, access_token: str, refresh_token: str) -> None:
    set_access_token_cookie(response, access_token)
    set_refresh_token_cookie(response, refresh_token)
