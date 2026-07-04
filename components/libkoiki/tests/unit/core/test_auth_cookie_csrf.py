from datetime import timedelta

import pytest
from starlette.requests import Request
from starlette.responses import Response

from libkoiki.core import auth_cookies
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


def test_auth_cookies_use_backend_settings(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ACCESS_COOKIE_NAME", "test_access")
    monkeypatch.setattr(settings, "AUTH_REFRESH_COOKIE_NAME", "test_refresh")
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", True)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SAMESITE", "strict")
    monkeypatch.setattr(settings, "AUTH_COOKIE_DOMAIN", None)

    response = Response()

    auth_cookies.set_auth_cookies(
        response,
        access_token="access-value",
        refresh_token="refresh-value",
    )

    set_cookie_headers = response.raw_headers
    cookie_text = "\n".join(
        value.decode("latin-1")
        for key, value in set_cookie_headers
        if key == b"set-cookie"
    )

    assert "test_access=access-value" in cookie_text
    assert "test_refresh=refresh-value" in cookie_text
    assert "HttpOnly" in cookie_text
    assert "Secure" in cookie_text
    assert "SameSite=strict" in cookie_text


def test_csrf_token_is_signed_and_must_match():
    token = generate_csrf_token()

    assert csrf_tokens_match(token, token)
    assert not csrf_tokens_match(token, None)
    assert not csrf_tokens_match(token, f"{token}tampered")
    assert not csrf_tokens_match("not.signed", "not.signed")


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
