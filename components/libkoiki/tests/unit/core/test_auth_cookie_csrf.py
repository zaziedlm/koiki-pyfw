from datetime import timedelta

import pytest
from starlette.requests import Request
from starlette.responses import Response

from libkoiki.core import auth_cookies
from libkoiki.core import csrf as csrf_module
from libkoiki.core.config import settings
from libkoiki.core.csrf import (
    CSRF_ERROR_CODE,
    csrf_tokens_match,
    generate_csrf_token,
    issue_csrf_token,
    validate_request_csrf,
)
from libkoiki.core.security import create_access_token, get_user_from_token


def _request(
    *,
    method: str = "GET",
    headers: list[tuple[bytes, bytes]] | None = None,
) -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": "/",
            "headers": headers or [],
        }
    )


def _set_cookie_lines(response: Response) -> list[str]:
    return [
        value.decode("latin-1")
        for key, value in response.raw_headers
        if key == b"set-cookie"
    ]


def test_auth_cookies_use_backend_settings(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ACCESS_COOKIE_NAME", "test_access")
    monkeypatch.setattr(settings, "AUTH_REFRESH_COOKIE_NAME", "test_refresh")
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", True)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SAMESITE", "strict")
    monkeypatch.setattr(settings, "AUTH_COOKIE_DOMAIN", None)
    monkeypatch.setattr(settings, "AUTH_COOKIE_PATH", "/")
    monkeypatch.setattr(settings, "AUTH_REFRESH_COOKIE_PATH", "/api/v1/auth/session")

    response = Response()

    auth_cookies.set_auth_cookies(
        response,
        access_token="access-value",
        refresh_token="refresh-value",
    )

    cookie_lines = _set_cookie_lines(response)
    access_cookie = next(line for line in cookie_lines if line.startswith("test_access="))
    refresh_cookie = next(line for line in cookie_lines if line.startswith("test_refresh="))

    assert "test_access=access-value" in access_cookie
    assert "HttpOnly" in access_cookie
    assert "Secure" in access_cookie
    assert "SameSite=strict" in access_cookie
    assert "Path=/" in access_cookie
    assert "test_refresh=refresh-value" in refresh_cookie
    assert "HttpOnly" in refresh_cookie
    assert "Secure" in refresh_cookie
    assert "SameSite=strict" in refresh_cookie
    assert "Path=/api/v1/auth/session" in refresh_cookie


def test_clear_auth_cookies_deletes_refresh_cookie_on_current_and_legacy_paths(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_COOKIE_PATH", "/")
    monkeypatch.setattr(settings, "AUTH_REFRESH_COOKIE_PATH", "/api/v1/auth/session")
    response = Response()

    auth_cookies.clear_auth_cookies(response)

    refresh_clear_cookies = (
        line
        for line in _set_cookie_lines(response)
        if line.startswith(f"{settings.AUTH_REFRESH_COOKIE_NAME}=")
    )

    refresh_clear_text = "\n".join(refresh_clear_cookies)
    assert f"{settings.AUTH_REFRESH_COOKIE_NAME}=\"\"" in refresh_clear_text
    assert "Path=/api/v1/auth/session" in refresh_clear_text
    assert "Path=/" in refresh_clear_text


def test_refresh_cookie_path_defaults_to_session_auth_route(monkeypatch):
    monkeypatch.setattr(settings, "API_PREFIX", "/api/v1")
    monkeypatch.setattr(settings, "AUTH_REFRESH_COOKIE_PATH", None)

    assert auth_cookies.refresh_cookie_path() == "/api/v1/auth/session"


def test_csrf_token_is_signed_and_must_match():
    token = generate_csrf_token()

    assert len(token.split(".")) == 3
    assert csrf_tokens_match(token, token)
    assert not csrf_tokens_match(token, None)
    assert not csrf_tokens_match(token, f"{token}tampered")
    assert not csrf_tokens_match("not.signed", "not.signed")


def test_csrf_token_expires(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_CSRF_COOKIE_MAX_AGE_SECONDS", 10)
    monkeypatch.setattr(csrf_module.time, "time", lambda: 1_000)
    token = generate_csrf_token()

    monkeypatch.setattr(csrf_module.time, "time", lambda: 1_011)

    assert not csrf_tokens_match(token, token)


def test_csrf_token_uses_separate_csrf_secret(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "jwt-secret-before")
    monkeypatch.setattr(settings, "AUTH_CSRF_SECRET", "csrf-secret")
    token = generate_csrf_token()

    monkeypatch.setattr(settings, "JWT_SECRET", "jwt-secret-after")
    assert csrf_tokens_match(token, token)

    monkeypatch.setattr(settings, "AUTH_CSRF_SECRET", "different-csrf-secret")
    assert not csrf_tokens_match(token, token)


def test_validate_request_csrf_only_requires_cookie_authenticated_unsafe_request():
    token = generate_csrf_token()
    request = _request(
        method="POST",
        headers=[
            (b"cookie", f"{settings.AUTH_CSRF_COOKIE_NAME}={token}".encode("latin-1")),
            (settings.AUTH_CSRF_HEADER_NAME.encode("latin-1"), token.encode("latin-1")),
        ],
    )
    request.state.auth_method = "cookie"

    validate_request_csrf(request)

    bearer_request = _request(method="POST")
    bearer_request.state.auth_method = "bearer"
    validate_request_csrf(bearer_request)

    get_request = _request(method="GET")
    get_request.state.auth_method = "cookie"
    validate_request_csrf(get_request)


def test_validate_request_csrf_rejects_invalid_cookie_authenticated_request():
    request = _request(method="POST")
    request.state.auth_method = "cookie"

    with pytest.raises(Exception) as exc_info:
        validate_request_csrf(request)

    assert getattr(exc_info.value, "status_code") == 403
    assert exc_info.value.detail["code"] == CSRF_ERROR_CODE


def test_issue_csrf_token_sets_js_readable_cookie():
    response = Response()
    token = issue_csrf_token(response)
    cookie_text = "\n".join(
        value.decode("latin-1")
        for key, value in response.raw_headers
        if key == b"set-cookie"
    )

    assert settings.AUTH_CSRF_COOKIE_NAME in cookie_text
    assert token in cookie_text
    assert "HttpOnly" not in cookie_text


@pytest.mark.asyncio
async def test_get_user_from_token_prefers_bearer_over_cookie():
    bearer_token = create_access_token("123", expires_delta=timedelta(minutes=5))
    cookie_token = create_access_token("456", expires_delta=timedelta(minutes=5))
    request = _request(
        headers=[
            (
                b"cookie",
                f"{settings.AUTH_ACCESS_COOKIE_NAME}={cookie_token}".encode("latin-1"),
            ),
        ]
    )

    user_id = await get_user_from_token(request, token=bearer_token)

    assert user_id == 123
    assert request.state.auth_method == "bearer"


@pytest.mark.asyncio
async def test_get_user_from_token_falls_back_to_cookie():
    cookie_token = create_access_token("456", expires_delta=timedelta(minutes=5))
    request = _request(
        headers=[
            (
                b"cookie",
                f"{settings.AUTH_ACCESS_COOKIE_NAME}={cookie_token}".encode("latin-1"),
            ),
        ]
    )

    user_id = await get_user_from_token(request, token=None)

    assert user_id == 456
    assert request.state.auth_method == "cookie"
