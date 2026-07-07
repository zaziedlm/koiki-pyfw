import base64
import hmac
import secrets
import time
from hashlib import sha256

from fastapi import HTTPException, Request, status
from starlette.responses import Response

from libkoiki.core.config import settings

CSRF_ERROR_CODE = "CSRF_TOKEN_INVALID"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
CSRF_CLOCK_SKEW_SECONDS = 60


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _sign(value: str) -> str:
    digest = hmac.new(
        settings.AUTH_CSRF_SECRET.encode("utf-8"),
        value.encode("utf-8"),
        sha256,
    ).digest()
    return _b64url(digest)


def generate_csrf_token() -> str:
    nonce = secrets.token_urlsafe(32)
    issued_at = str(int(time.time()))
    payload = f"{nonce}.{issued_at}"
    return f"{payload}.{_sign(payload)}"


def is_valid_csrf_token(token: str | None) -> bool:
    if not token:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    nonce, issued_at_text, signature = parts
    if not nonce or not issued_at_text or not signature:
        return False

    try:
        issued_at = int(issued_at_text)
    except ValueError:
        return False

    now = int(time.time())
    if issued_at > now + CSRF_CLOCK_SKEW_SECONDS:
        return False
    if now - issued_at > settings.AUTH_CSRF_COOKIE_MAX_AGE_SECONDS:
        return False

    payload = f"{nonce}.{issued_at_text}"
    expected_signature = _sign(payload)
    return hmac.compare_digest(signature, expected_signature)


def csrf_tokens_match(cookie_token: str | None, header_token: str | None) -> bool:
    if not cookie_token or not header_token:
        return False
    if not is_valid_csrf_token(cookie_token) or not is_valid_csrf_token(header_token):
        return False
    return hmac.compare_digest(cookie_token, header_token)


def set_csrf_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.AUTH_CSRF_COOKIE_NAME,
        token,
        httponly=False,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        max_age=settings.AUTH_CSRF_COOKIE_MAX_AGE_SECONDS,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
    )


def issue_csrf_token(response: Response) -> str:
    token = generate_csrf_token()
    set_csrf_cookie(response, token)
    return token


def request_uses_cookie_auth(request: Request) -> bool:
    return getattr(request.state, "auth_method", None) == "cookie"


def should_validate_csrf(request: Request) -> bool:
    return request.method.upper() not in SAFE_METHODS and request_uses_cookie_auth(request)


def validate_request_csrf(request: Request) -> None:
    if not should_validate_csrf(request):
        return

    require_valid_csrf_token(request)


def require_valid_csrf_token(request: Request) -> None:
    """Request の CSRF cookie/header pair を必ず検証する。"""

    cookie_token = request.cookies.get(settings.AUTH_CSRF_COOKIE_NAME)
    header_token = request.headers.get(settings.AUTH_CSRF_HEADER_NAME)
    if csrf_tokens_match(cookie_token, header_token):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "message": "CSRF token validation failed",
            "code": CSRF_ERROR_CODE,
        },
    )
