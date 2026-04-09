import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


@pytest.fixture
def middleware_module(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("APP_ENV", "testing")

    config_module = importlib.import_module("libkoiki.core.config")
    importlib.reload(config_module)

    logging_module = importlib.import_module("libkoiki.core.logging")
    importlib.reload(logging_module)

    module = importlib.import_module("libkoiki.core.middleware")
    return importlib.reload(module)


def _build_app(middleware_module, endpoint):
    app = FastAPI()
    app.add_middleware(middleware_module.SecurityHeadersMiddleware)
    app.add_middleware(middleware_module.AuditLogMiddleware)
    app.add_middleware(middleware_module.RequestContextLogMiddleware)
    app.get("/todos/{todo_id}")(endpoint)
    app.get("/health")(lambda: {"status": "ok"})
    return app


class TestAuditMiddleware:
    def test_audit_middleware_generates_request_id_and_logs_policy_fields(
        self,
        middleware_module,
    ):
        mock_audit_logger = MagicMock()
        middleware_module.audit_logger = mock_audit_logger

        async def endpoint(request: Request, todo_id: str):
            request.state.current_user = SimpleNamespace(id=42, email="user@example.com")
            request.state.auth_method = "bearer"
            return {"todo_id": todo_id}

        app = _build_app(middleware_module, endpoint)

        with TestClient(app) as client:
            response = client.get("/todos/123")

        assert response.status_code == 200
        assert response.headers["X-Request-ID"]

        audit_kwargs = mock_audit_logger.info.call_args.kwargs
        assert audit_kwargs["audit"] is True
        assert audit_kwargs["actor.user_id"] == 42
        assert audit_kwargs["actor.email"] == "user@example.com"
        assert audit_kwargs["actor.auth_method"] == "bearer"
        assert audit_kwargs["http.method"] == "GET"
        assert audit_kwargs["http.path"] == "/todos/123"
        assert audit_kwargs["http.request_id"] == response.headers["X-Request-ID"]
        assert audit_kwargs["http.status_code"] == 200
        assert audit_kwargs["target.resource_type"] == "todos"
        assert audit_kwargs["target.resource_id"] == "123"
        assert audit_kwargs["outcome"] == "success"
        assert "http.query" not in audit_kwargs

    def test_audit_middleware_preserves_incoming_request_id(
        self,
        middleware_module,
    ):
        mock_audit_logger = MagicMock()
        middleware_module.audit_logger = mock_audit_logger

        async def endpoint(request: Request, todo_id: str):
            return {"todo_id": todo_id}

        app = _build_app(middleware_module, endpoint)

        with TestClient(app) as client:
            response = client.get("/todos/999", headers={"X-Request-ID": "req-fixed-001"})

        assert response.headers["X-Request-ID"] == "req-fixed-001"
        audit_kwargs = mock_audit_logger.info.call_args.kwargs
        assert audit_kwargs["http.request_id"] == "req-fixed-001"

    def test_audit_middleware_skips_excluded_paths(
        self,
        middleware_module,
    ):
        mock_audit_logger = MagicMock()
        middleware_module.audit_logger = mock_audit_logger

        app = FastAPI()
        app.add_middleware(middleware_module.AuditLogMiddleware)
        app.add_middleware(middleware_module.RequestContextLogMiddleware)

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        with TestClient(app) as client:
            response = client.get("/health")

        assert response.status_code == 200
        mock_audit_logger.info.assert_not_called()

    def test_audit_middleware_does_not_include_query_or_sensitive_headers(
        self,
        middleware_module,
    ):
        mock_audit_logger = MagicMock()
        middleware_module.audit_logger = mock_audit_logger

        async def endpoint(request: Request, todo_id: str):
            request.state.current_user = SimpleNamespace(id=8, email="audit@example.com")
            request.state.auth_method = "bearer"
            return {"todo_id": todo_id}

        app = _build_app(middleware_module, endpoint)

        with TestClient(app) as client:
            response = client.get(
                "/todos/777?token=should-not-appear",
                headers={
                    "Authorization": "Bearer secret-token",
                    "Cookie": "session=secret-cookie",
                    "X-Request-ID": "req-audit-sensitive-001",
                },
            )

        assert response.status_code == 200
        audit_kwargs = mock_audit_logger.info.call_args.kwargs
        assert "http.query" not in audit_kwargs
        assert "authorization" not in audit_kwargs
        assert "cookie" not in audit_kwargs
        assert "token" not in str(audit_kwargs).lower()

    def test_access_log_uses_same_request_context_source(
        self,
        middleware_module,
    ):
        mock_access_logger = MagicMock()
        middleware_module.access_logger = mock_access_logger

        app = FastAPI()
        app.add_middleware(middleware_module.AccessLogMiddleware)
        app.add_middleware(middleware_module.RequestContextLogMiddleware)

        @app.get("/todos/{todo_id}")
        async def endpoint(todo_id: str):
            return {"todo_id": todo_id}

        with TestClient(app) as client:
            response = client.get("/todos/321", headers={"X-Request-ID": "req-access-001"})

        assert response.status_code == 200
        access_kwargs = mock_access_logger.info.call_args.kwargs
        assert access_kwargs["method"] == "GET"
        assert access_kwargs["path"] == "/todos/321"
        assert access_kwargs["request_id"] == "req-access-001"
