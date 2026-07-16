"""Cookie session auth contract integration tests."""
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from libkoiki.core.config import settings


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}@example.com"


def _register_user(client: TestClient, *, email: str, password: str = "TestPass123@") -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": email.split("@")[0][:50],
            "email": email,
            "password": password,
            "full_name": "Session User",
        },
    )
    assert response.status_code == 201, response.text


def _csrf_header(client: TestClient) -> dict[str, str]:
    token = client.cookies.get(settings.AUTH_CSRF_COOKIE_NAME)
    assert token
    return {settings.AUTH_CSRF_HEADER_NAME: token}


def _cookie_text(response) -> str:
    return "\n".join(response.headers.get_list("set-cookie"))


def _bootstrap_csrf(client: TestClient) -> str:
    response = client.get("/api/v1/auth/session/csrf")
    assert response.status_code == 200, response.text
    data = response.json()
    token = data["csrf_token"]
    assert data["header_name"] == settings.AUTH_CSRF_HEADER_NAME
    assert client.cookies.get(settings.AUTH_CSRF_COOKIE_NAME) == token
    return token


def _session_login(client: TestClient, *, email: str, password: str = "TestPass123@"):
    _bootstrap_csrf(client)
    response = client.post(
        "/api/v1/auth/session/login",
        json={"email": email, "password": password},
        headers=_csrf_header(client),
    )
    assert response.status_code == 200, response.text
    return response


@pytest.mark.integration
@pytest.mark.db_integration
class TestAuthSessionAPI:
    def test_session_password_login_sets_cookie_and_hides_tokens(self, test_client: TestClient):
        email = _email("session-login")
        _register_user(test_client, email=email)

        response = _session_login(test_client, email=email)
        data = response.json()

        assert data["message"] == "Login successful"
        assert data["user"]["email"] == email
        assert data["location"] == "/dashboard"
        assert "access_token" not in str(data)
        assert "refresh_token" not in str(data)
        assert test_client.cookies.get(settings.AUTH_ACCESS_COOKIE_NAME)
        assert test_client.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
        assert test_client.cookies.get(settings.AUTH_CSRF_COOKIE_NAME)

    def test_cookie_auth_resolves_current_user(self, test_client: TestClient):
        email = _email("session-me")
        _register_user(test_client, email=email)
        _session_login(test_client, email=email)

        response = test_client.get("/api/v1/auth/session/me")

        assert response.status_code == 200, response.text
        assert response.json()["email"] == email

    def test_cookie_authenticated_update_requires_valid_csrf(self, test_client: TestClient):
        email = _email("session-csrf")
        _register_user(test_client, email=email)
        _session_login(test_client, email=email)

        invalid_response = test_client.put(
            "/api/v1/users/me",
            json={"full_name": "Rejected Name"},
            headers={settings.AUTH_CSRF_HEADER_NAME: "invalid-token"},
        )
        assert invalid_response.status_code == 403

        valid_response = test_client.put(
            "/api/v1/users/me",
            json={"full_name": "Updated Name"},
            headers=_csrf_header(test_client),
        )
        assert valid_response.status_code == 200, valid_response.text
        assert valid_response.json()["full_name"] == "Updated Name"

    def test_bearer_authenticated_update_does_not_require_csrf(self, test_client: TestClient):
        email = _email("bearer-no-csrf")
        _register_user(test_client, email=email)
        login_response = test_client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "TestPass123@"},
        )
        assert login_response.status_code == 200, login_response.text
        token = login_response.json()["access_token"]

        response = test_client.put(
            "/api/v1/users/me",
            json={"full_name": "Bearer Updated"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        assert response.json()["full_name"] == "Bearer Updated"

    def test_session_refresh_rotates_cookie_and_hides_tokens(self, test_client: TestClient):
        email = _email("session-refresh")
        _register_user(test_client, email=email)
        _session_login(test_client, email=email)
        old_refresh_cookie = test_client.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)

        response = test_client.post(
            "/api/v1/auth/session/refresh",
            headers=_csrf_header(test_client),
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data == {"message": "Token refreshed"}
        assert "access_token" not in str(data)
        assert "refresh_token" not in str(data)
        assert test_client.cookies.get(settings.AUTH_ACCESS_COOKIE_NAME)
        assert test_client.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
        assert test_client.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME) != old_refresh_cookie

    def test_session_refresh_failure_clears_cookies(self, test_client: TestClient):
        _bootstrap_csrf(test_client)
        test_client.cookies.set(settings.AUTH_REFRESH_COOKIE_NAME, "invalid-refresh-token")
        test_client.cookies.set(settings.AUTH_ACCESS_COOKIE_NAME, "invalid-access-token")

        response = test_client.post(
            "/api/v1/auth/session/refresh",
            headers=_csrf_header(test_client),
        )

        assert response.status_code == 401
        assert response.json()["data"]["code"] == "REFRESH_TOKEN_INVALID"
        cookie_text = _cookie_text(response)
        assert settings.AUTH_ACCESS_COOKIE_NAME in cookie_text
        assert settings.AUTH_REFRESH_COOKIE_NAME in cookie_text
        assert "Max-Age=0" in cookie_text

    def test_session_logout_clears_cookies_and_me_returns_401(self, test_client: TestClient):
        email = _email("session-logout")
        _register_user(test_client, email=email)
        _session_login(test_client, email=email)

        response = test_client.post(
            "/api/v1/auth/session/logout",
            headers=_csrf_header(test_client),
        )
        assert response.status_code == 200, response.text
        assert response.json()["message"] == "Logout successful"

        me_response = test_client.get("/api/v1/auth/session/me")
        assert me_response.status_code == 401

    def test_users_api_permission_parity_with_cookie_auth(self, test_client: TestClient):
        email = _email("session-permission")
        _register_user(test_client, email=email)
        _session_login(test_client, email=email)

        response = test_client.get("/api/v1/users")

        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    def test_existing_token_login_and_refresh_contract_still_returns_tokens(
        self, test_client: TestClient
    ):
        email = _email("token-compat")
        _register_user(test_client, email=email)
        login_response = test_client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "TestPass123@"},
        )
        assert login_response.status_code == 200, login_response.text
        login_data = login_response.json()
        assert login_data["access_token"]
        assert login_data["refresh_token"]

        refresh_response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login_data["refresh_token"]},
        )

        assert refresh_response.status_code == 200, refresh_response.text
        refresh_data = refresh_response.json()
        assert refresh_data["access_token"]
        assert refresh_data["refresh_token"]

    def test_session_sso_and_saml_exchange_set_cookies_without_tokens(
        self, test_client: TestClient, monkeypatch
    ):
        from koiki_ref_app.api.v1.endpoints import saml_auth, sso_auth
        from types import SimpleNamespace
        from datetime import datetime, timezone

        user = SimpleNamespace(
            id=1,
            username="federated",
            email="federated@example.com",
            full_name="Federated User",
            is_active=True,
            is_superuser=False,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            roles=[],
        )
        monkeypatch.setattr(
            sso_auth,
            "authenticate_sso_and_create_token_pair",
            AsyncMock(return_value=(user, "sso-access", "sso-refresh", 3600)),
        )
        monkeypatch.setattr(
            saml_auth,
            "exchange_saml_login_ticket_and_create_token_pair",
            AsyncMock(return_value=(user, "saml-access", "saml-refresh", 3600)),
        )

        _bootstrap_csrf(test_client)
        sso_response = test_client.post(
            "/api/v1/auth/session/sso/login",
            json={
                "authorization_code": "auth-code",
                "code_verifier": "verifier",
                "redirect_uri": "https://app.example.com/sso/callback",
                "nonce": "nonce-123",
                "state": "signed-state",
            },
            headers=_csrf_header(test_client),
        )
        assert sso_response.status_code == 200, sso_response.text
        assert "access_token" not in str(sso_response.json())
        assert "refresh_token" not in str(sso_response.json())
        assert test_client.cookies.get(settings.AUTH_ACCESS_COOKIE_NAME)
        assert test_client.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)

        saml_response = test_client.post(
            "/api/v1/auth/session/saml/login",
            json={
                "login_ticket": "signed-ticket",
                "relay_state": "signed-relay-state",
            },
            headers=_csrf_header(test_client),
        )
        assert saml_response.status_code == 200, saml_response.text
        assert "access_token" not in str(saml_response.json())
        assert "refresh_token" not in str(saml_response.json())
        assert test_client.cookies.get(settings.AUTH_ACCESS_COOKIE_NAME)
        assert test_client.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
