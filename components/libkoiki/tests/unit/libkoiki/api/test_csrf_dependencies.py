from types import SimpleNamespace

import pytest
from starlette.requests import Request

from libkoiki.api import dependencies
from libkoiki.core.config import settings
from libkoiki.core.csrf import CSRF_ERROR_CODE, generate_csrf_token


def _request(
    *,
    method: str = "POST",
    csrf_token: str | None = None,
    auth_method: str = "cookie",
) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if csrf_token:
        headers.extend(
            [
                (
                    b"cookie",
                    f"{settings.AUTH_CSRF_COOKIE_NAME}={csrf_token}".encode("latin-1"),
                ),
                (
                    settings.AUTH_CSRF_HEADER_NAME.encode("latin-1"),
                    csrf_token.encode("latin-1"),
                ),
            ]
        )
    request = Request(
        {
            "type": "http",
            "method": method,
            "path": "/api/v1/protected",
            "headers": headers,
        }
    )
    request.state.auth_method = auth_method
    return request


class FakeUserRepository:
    def __init__(self, user):
        self.user = user
        self.session = None
        self.loaded_user_id = None

    def set_session(self, db):
        self.session = db

    async def get_user_with_roles_permissions(self, user_id):
        self.loaded_user_id = user_id
        return self.user


@pytest.mark.asyncio
async def test_active_user_dependency_rejects_cookie_unsafe_request_without_csrf(
    monkeypatch,
):
    user = SimpleNamespace(id=123, email="user@example.com", is_active=True)
    repo = FakeUserRepository(user)
    monkeypatch.setattr(dependencies, "UserRepository", lambda: repo)

    with pytest.raises(Exception) as exc_info:
        await dependencies.get_current_active_user(
            request=_request(auth_method="cookie"),
            user_id=123,
            db=object(),
        )

    assert getattr(exc_info.value, "status_code") == 403
    assert exc_info.value.detail["code"] == CSRF_ERROR_CODE
    assert repo.loaded_user_id is None


@pytest.mark.asyncio
async def test_active_user_dependency_allows_cookie_unsafe_request_with_valid_csrf(
    monkeypatch,
):
    user = SimpleNamespace(id=123, email="user@example.com", is_active=True)
    repo = FakeUserRepository(user)
    monkeypatch.setattr(dependencies, "UserRepository", lambda: repo)
    token = generate_csrf_token()

    result = await dependencies.get_current_active_user(
        request=_request(auth_method="cookie", csrf_token=token),
        user_id=123,
        db=object(),
    )

    assert result is user
    assert repo.loaded_user_id == 123


@pytest.mark.asyncio
async def test_active_user_dependency_does_not_require_csrf_for_bearer_auth(
    monkeypatch,
):
    user = SimpleNamespace(id=123, email="user@example.com", is_active=True)
    repo = FakeUserRepository(user)
    monkeypatch.setattr(dependencies, "UserRepository", lambda: repo)

    result = await dependencies.get_current_active_user(
        request=_request(auth_method="bearer"),
        user_id=123,
        db=object(),
    )

    assert result is user
    assert repo.loaded_user_id == 123
