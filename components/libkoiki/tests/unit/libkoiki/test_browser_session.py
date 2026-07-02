from starlette.requests import Request
from starlette.responses import Response

from libkoiki.core.browser_session import (
    has_valid_csrf_token,
    set_auth_cookies,
    set_csrf_cookie,
)
from libkoiki.core.config import settings


def make_request(cookie: str = "", header_token: str | None = None) -> Request:
    headers = []
    if cookie:
        headers.append((b"cookie", cookie.encode()))
    if header_token:
        headers.append((settings.BROWSER_CSRF_HEADER_NAME.encode(), header_token.encode()))
    return Request({"type": "http", "method": "POST", "path": "/", "headers": headers})


def test_csrf_requires_matching_cookie_and_header() -> None:
    token = "matching-token"
    request = make_request(f"{settings.BROWSER_CSRF_COOKIE_NAME}={token}", token)
    assert has_valid_csrf_token(request) is True


def test_csrf_rejects_missing_or_mismatched_token() -> None:
    request = make_request(f"{settings.BROWSER_CSRF_COOKIE_NAME}=cookie-token", "header-token")
    assert has_valid_csrf_token(request) is False
    assert has_valid_csrf_token(make_request()) is False


def test_session_helpers_mark_auth_tokens_http_only() -> None:
    response = Response()
    set_auth_cookies(response, access_token="access", refresh_token="refresh")
    set_csrf_cookie(response, "csrf")
    headers = b"\n".join(value for key, value in response.raw_headers if key == b"set-cookie").decode()

    assert f"{settings.BROWSER_ACCESS_TOKEN_COOKIE_NAME}=access" in headers
    assert f"{settings.BROWSER_REFRESH_TOKEN_COOKIE_NAME}=refresh" in headers
    assert "HttpOnly" in headers
    assert f"{settings.BROWSER_CSRF_COOKIE_NAME}=csrf" in headers
