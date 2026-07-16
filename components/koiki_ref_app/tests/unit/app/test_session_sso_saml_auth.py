import importlib
import inspect
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from libkoiki.core.config import settings
from libkoiki.core.csrf import generate_csrf_token


def _request(csrf_token: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if csrf_token:
        cookie_header = f"{settings.AUTH_CSRF_COOKIE_NAME}={csrf_token}"
        headers.append((b"cookie", cookie_header.encode("latin-1")))
        headers.append(
            (
                settings.AUTH_CSRF_HEADER_NAME.encode("latin-1"),
                csrf_token.encode("latin-1"),
            )
        )

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/session/sso/login",
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
async def test_session_sso_login_sets_cookies_without_token_body(monkeypatch):
    module = importlib.reload(importlib.import_module("app.api.v1.endpoints.sso_auth"))
    from koiki_ref_app.schemas.sso import SSOLoginRequest

    helper = AsyncMock(return_value=(_user(), "access-token", "refresh-token", 3600))
    monkeypatch.setattr(module, "authenticate_sso_and_create_token_pair", helper)

    endpoint = inspect.unwrap(module.session_sso_login)
    response = await endpoint(
        request=_request(csrf_token=generate_csrf_token()),
        sso_request=SSOLoginRequest(
            authorization_code="auth-code",
            code_verifier="verifier",
            redirect_uri="https://app.example.com/sso/callback",
            nonce="nonce-123",
            state="signed-state",
        ),
        sso_service=object(),
        db=object(),
    )

    body = _json_body(response)
    cookie_text = _cookie_text(response)

    assert body["message"] == "SSO login successful"
    assert body["user"]["email"] == "session@example.com"
    assert body["location"] == "/dashboard"
    assert "access_token" not in str(body)
    assert "refresh_token" not in str(body)
    assert settings.AUTH_ACCESS_COOKIE_NAME in cookie_text
    assert settings.AUTH_REFRESH_COOKIE_NAME in cookie_text
    assert settings.AUTH_CSRF_COOKIE_NAME in cookie_text


@pytest.mark.asyncio
async def test_session_sso_login_requires_csrf(monkeypatch):
    module = importlib.reload(importlib.import_module("app.api.v1.endpoints.sso_auth"))
    from koiki_ref_app.schemas.sso import SSOLoginRequest

    helper = AsyncMock()
    monkeypatch.setattr(module, "authenticate_sso_and_create_token_pair", helper)

    endpoint = inspect.unwrap(module.session_sso_login)
    with pytest.raises(HTTPException) as exc_info:
        await endpoint(
            request=_request(),
            sso_request=SSOLoginRequest(
                authorization_code="auth-code",
                code_verifier="verifier",
                redirect_uri="https://app.example.com/sso/callback",
                nonce="nonce-123",
                state="signed-state",
            ),
            sso_service=object(),
            db=object(),
        )

    assert exc_info.value.status_code == 403
    helper.assert_not_awaited()


@pytest.mark.asyncio
async def test_session_saml_login_sets_cookies_without_token_body(monkeypatch):
    module = importlib.reload(importlib.import_module("app.api.v1.endpoints.saml_auth"))
    from koiki_ref_app.schemas.saml import SAMLLoginTicketRequest

    helper = AsyncMock(return_value=(_user(), "access-token", "refresh-token", 3600))
    monkeypatch.setattr(module, "exchange_saml_login_ticket_and_create_token_pair", helper)

    endpoint = inspect.unwrap(module.session_saml_login)
    response = await endpoint(
        request=_request(csrf_token=generate_csrf_token()),
        login_request=SAMLLoginTicketRequest(
            login_ticket="signed-ticket",
            relay_state="signed-relay-state",
        ),
        saml_service=object(),
        db=object(),
    )

    body = _json_body(response)
    cookie_text = _cookie_text(response)

    assert body["message"] == "SAML login successful"
    assert body["user"]["email"] == "session@example.com"
    assert body["location"] == "/dashboard"
    assert "access_token" not in str(body)
    assert "refresh_token" not in str(body)
    assert settings.AUTH_ACCESS_COOKIE_NAME in cookie_text
    assert settings.AUTH_REFRESH_COOKIE_NAME in cookie_text
    assert settings.AUTH_CSRF_COOKIE_NAME in cookie_text


@pytest.mark.asyncio
async def test_session_saml_login_requires_csrf(monkeypatch):
    module = importlib.reload(importlib.import_module("app.api.v1.endpoints.saml_auth"))
    from koiki_ref_app.schemas.saml import SAMLLoginTicketRequest

    helper = AsyncMock()
    monkeypatch.setattr(module, "exchange_saml_login_ticket_and_create_token_pair", helper)

    endpoint = inspect.unwrap(module.session_saml_login)
    with pytest.raises(HTTPException) as exc_info:
        await endpoint(
            request=_request(),
            login_request=SAMLLoginTicketRequest(
                login_ticket="signed-ticket",
                relay_state="signed-relay-state",
            ),
            saml_service=object(),
            db=object(),
        )

    assert exc_info.value.status_code == 403
    helper.assert_not_awaited()
