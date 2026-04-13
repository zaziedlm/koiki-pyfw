import importlib
from types import SimpleNamespace

import pytest


@pytest.fixture
def dependencies_module(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("APP_ENV", "testing")

    config_module = importlib.import_module("libkoiki.core.config")
    importlib.reload(config_module)

    module = importlib.import_module("libkoiki.api.dependencies")
    return importlib.reload(module)


class TestAuditDependencyWiring:
    @pytest.mark.asyncio
    async def test_get_current_active_user_binds_current_user_to_request_state(
        self,
        dependencies_module,
        monkeypatch,
    ):
        current_user = SimpleNamespace(id=7, email="user@example.com", is_active=True)

        class FakeUserRepository:
            def set_session(self, db):
                self.db = db

            async def get_user_with_roles_permissions(self, user_id):
                assert user_id == 7
                return current_user

        monkeypatch.setattr(dependencies_module, "UserRepository", FakeUserRepository)
        request = SimpleNamespace(state=SimpleNamespace())

        result = await dependencies_module.get_current_active_user(
            request=request,
            user_id=7,
            db=object(),
        )

        assert result is current_user
        assert request.state.current_user is current_user
        assert request.state.auth_method == "bearer"
        assert request.state.audit_user_id == 7
        assert request.state.audit_user_email == "user@example.com"
