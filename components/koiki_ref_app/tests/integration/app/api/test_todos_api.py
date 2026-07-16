"""Todo API optimistic locking integration tests."""
from uuid import uuid4

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
            "full_name": "Todo User",
        },
    )
    assert response.status_code == 201, response.text


def _csrf_header(client: TestClient) -> dict[str, str]:
    token = client.cookies.get(settings.AUTH_CSRF_COOKIE_NAME)
    assert token
    return {settings.AUTH_CSRF_HEADER_NAME: token}


def _bootstrap_csrf(client: TestClient) -> None:
    response = client.get("/api/v1/auth/session/csrf")
    assert response.status_code == 200, response.text


def _session_login(client: TestClient, *, email: str, password: str = "TestPass123@"):
    _bootstrap_csrf(client)
    response = client.post(
        "/api/v1/auth/session/login",
        json={"email": email, "password": password},
        headers=_csrf_header(client),
    )
    assert response.status_code == 200, response.text
    return response


def _create_todo(client: TestClient, *, title: str = "Write report") -> dict:
    response = client.post(
        "/api/v1/todos",
        json={"title": title},
        headers=_csrf_header(client),
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.integration
@pytest.mark.db_integration
class TestTodosAPIOptimisticLocking:
    def test_update_with_current_version_succeeds_and_increments_version(self, test_client: TestClient):
        email = _email("todo-version")
        _register_user(test_client, email=email)
        _session_login(test_client, email=email)

        todo = _create_todo(test_client)
        assert todo["version"] == 1

        update_response = test_client.put(
            f"/api/v1/todos/{todo['id']}",
            json={"title": "Write report v2", "version": todo["version"]},
            headers=_csrf_header(test_client),
        )

        assert update_response.status_code == 200, update_response.text
        updated = update_response.json()
        assert updated["title"] == "Write report v2"
        assert updated["version"] == 2

    def test_update_with_stale_version_returns_409(self, test_client: TestClient):
        email = _email("todo-conflict")
        _register_user(test_client, email=email)
        _session_login(test_client, email=email)

        todo = _create_todo(test_client)

        first_update = test_client.put(
            f"/api/v1/todos/{todo['id']}",
            json={"title": "First update", "version": todo["version"]},
            headers=_csrf_header(test_client),
        )
        assert first_update.status_code == 200, first_update.text

        stale_update = test_client.put(
            f"/api/v1/todos/{todo['id']}",
            json={"title": "Stale update", "version": todo["version"]},
            headers=_csrf_header(test_client),
        )

        assert stale_update.status_code == 409, stale_update.text
