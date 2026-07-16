import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from libkoiki.core.config import settings
from libkoiki.core.csrf import generate_csrf_token


def _request(
    *,
    method: str = "POST",
    csrf_token: str | None = None,
    cookies: dict[str, str] | None = None,
) -> Request:
    cookie_values = cookies.copy() if cookies else {}
    if csrf_token:
        cookie_values[settings.AUTH_CSRF_COOKIE_NAME] = csrf_token

    headers: list[tuple[bytes, bytes]] = []
    if cookie_values:
        cookie_header = "; ".join(f"{key}={value}" for key, value in cookie_values.items())
        headers.append((b"cookie", cookie_header.encode("latin-1")))
    if csrf_token:
        headers.append((settings.AUTH_CSRF_HEADER_NAME.encode("latin-1"), csrf_token.encode("latin-1")))

    return Request(
        {
            "type": "http",
            "method": method,
            "path": "/api/v1/auth/session/login",
            "headers": headers,
            "client": ("127.0.0.1", 12345),
        }
    )


def _user():
    return SimpleNamespace(
        id=1,
        username="sessionuser",
        email="session@example.com",
        full_name="Session User",
        is_active=True,
        is_superuser=False,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        roles=[],
    )


def _json_body(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


def _cookie_text(response) -> str:
    return "\n".join(
        value.decode("latin-1")
        for key, value in response.raw_headers
        if key == b"set-cookie"
    )


@pytest.mark.asyncio
async def test_session_login_sets_cookies_without_token_body(monkeypatch):
    from libkoiki.api.v1.endpoints import auth_session
    from libkoiki.schemas.auth_session import SessionLoginRequest

    monkeypatch.setattr(
        auth_session,
        "authenticate_password_and_create_token_pair",
        AsyncMock(return_value=(_user(), "access-token", "refresh-token", 3600)),
    )

    response = await auth_session.session_login(
        request=_request(csrf_token=generate_csrf_token()),
        login_data=SessionLoginRequest(email="session@example.com", password="TestPass123@"),
        user_service=object(),
        auth_service=object(),
        login_security_service=object(),
        db=object(),
    )

    body = _json_body(response)
    cookie_text = _cookie_text(response)

    assert body["message"] == "Login successful"
    assert body["user"]["email"] == "session@example.com"
    assert body["location"] == "/dashboard"
    assert "access_token" not in str(body)
    assert "refresh_token" not in str(body)
    assert settings.AUTH_ACCESS_COOKIE_NAME in cookie_text
    assert settings.AUTH_REFRESH_COOKIE_NAME in cookie_text
    assert settings.AUTH_CSRF_COOKIE_NAME in cookie_text
    assert "HttpOnly" in cookie_text


@pytest.mark.asyncio
async def test_session_register_does_not_set_auth_cookies():
    from libkoiki.api.v1.endpoints import auth_session
    from libkoiki.schemas.user import UserCreate

    user_service = SimpleNamespace(create_user=AsyncMock(return_value=_user()))

    response = await auth_session.session_register(
        request=_request(csrf_token=generate_csrf_token()),
        user_in=UserCreate(
            username="sessionuser",
            email="session@example.com",
            full_name="Session User",
            password="TestPass123@",
        ),
        user_service=user_service,
        db=object(),
    )

    cookie_text = _cookie_text(response)
    body = _json_body(response)

    assert response.status_code == 201
    assert body["message"] == "User registered successfully"
    assert body["location"] == "/auth/login"
    assert settings.AUTH_ACCESS_COOKIE_NAME not in cookie_text
    assert settings.AUTH_REFRESH_COOKIE_NAME not in cookie_text
    assert settings.AUTH_CSRF_COOKIE_NAME in cookie_text


@pytest.mark.asyncio
async def test_session_login_requires_csrf():
    from libkoiki.api.v1.endpoints import auth_session
    from libkoiki.schemas.auth_session import SessionLoginRequest

    with pytest.raises(HTTPException) as exc_info:
        await auth_session.session_login(
            request=_request(),
            login_data=SessionLoginRequest(email="session@example.com", password="TestPass123@"),
            user_service=object(),
            auth_service=object(),
            login_security_service=object(),
            db=object(),
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_session_refresh_rotates_cookies_without_token_body():
    from libkoiki.api.v1.endpoints import auth_session

    auth_service = SimpleNamespace(
        refresh_access_token=AsyncMock(return_value=("new-access", "new-refresh", 3600))
    )

    response = await auth_session.session_refresh(
        request=_request(
            csrf_token=generate_csrf_token(),
            cookies={settings.AUTH_REFRESH_COOKIE_NAME: "old-refresh"},
        ),
        auth_service=auth_service,
        db=object(),
    )

    body = _json_body(response)
    cookie_text = _cookie_text(response)

    assert response.status_code == 200
    assert body == {"message": "Token refreshed"}
    assert "access_token" not in str(body)
    assert "refresh_token" not in str(body)
    assert settings.AUTH_ACCESS_COOKIE_NAME in cookie_text
    assert settings.AUTH_REFRESH_COOKIE_NAME in cookie_text
    assert settings.AUTH_CSRF_COOKIE_NAME in cookie_text
    auth_service.refresh_access_token.assert_awaited_once()
    assert auth_service.refresh_access_token.await_args.kwargs["refresh_token"] == "old-refresh"
    assert auth_service.refresh_access_token.await_args.kwargs["enable_rotation"] is True


@pytest.mark.asyncio
async def test_session_refresh_missing_cookie_clears_auth_cookies():
    from libkoiki.api.v1.endpoints import auth_session

    response = await auth_session.session_refresh(
        request=_request(csrf_token=generate_csrf_token()),
        auth_service=object(),
        db=object(),
    )

    body = _json_body(response)
    cookie_text = _cookie_text(response)

    assert response.status_code == 401
    assert body["data"]["code"] == "REFRESH_TOKEN_MISSING"
    assert settings.AUTH_ACCESS_COOKIE_NAME in cookie_text
    assert "Max-Age=0" in cookie_text


@pytest.mark.asyncio
async def test_session_logout_revokes_refresh_cookie_and_clears_cookies():
    from libkoiki.api.v1.endpoints import auth_session

    db = object()
    auth_service = SimpleNamespace(revoke_refresh_token=AsyncMock(return_value=True))
    response = await auth_session.session_logout(
        request=_request(
            csrf_token=generate_csrf_token(),
            cookies={settings.AUTH_REFRESH_COOKIE_NAME: "refresh-token"},
        ),
        auth_service=auth_service,
        db=db,
    )

    body = _json_body(response)
    cookie_text = _cookie_text(response)

    assert body["message"] == "Logout successful"
    auth_service.revoke_refresh_token.assert_awaited_once_with("refresh-token", db)
    assert settings.AUTH_ACCESS_COOKIE_NAME in cookie_text
    assert settings.AUTH_REFRESH_COOKIE_NAME in cookie_text
    assert "Max-Age=0" in cookie_text


@pytest.mark.asyncio
async def test_session_me_returns_current_user():
    from libkoiki.api.v1.endpoints import auth_session

    response = await auth_session.session_me(current_user=_user())

    assert response.email == "session@example.com"
    assert response.username == "sessionuser"
