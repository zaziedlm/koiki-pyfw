import importlib
import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from libkoiki.core.exceptions import ValidationException


@pytest.fixture
def logging_setup(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("APP_ENV", "testing")

    config_module = importlib.import_module("libkoiki.core.config")
    importlib.reload(config_module)

    logging_module = importlib.import_module("libkoiki.core.logging")
    logging_module = importlib.reload(logging_module)
    logging_module.setup_logging()
    return logging_module


@pytest.fixture
def error_handlers_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.core.error_handlers")
    return importlib.reload(module)


@pytest.fixture
def db_session_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.db.session")
    return importlib.reload(module)


@pytest.fixture
def auth_decorators_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.core.auth_decorators")
    return importlib.reload(module)


@pytest.fixture
def transaction_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.core.transaction")
    return importlib.reload(module)


@pytest.fixture
def security_metrics_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.core.security_metrics")
    return importlib.reload(module)


@pytest.fixture
def users_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.api.v1.endpoints.users")
    return importlib.reload(module)


@pytest.fixture
def security_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.core.security")
    return importlib.reload(module)


def _request(path: str = "/users", method: str = "POST", client_host: str = "192.168.1.25"):
    return SimpleNamespace(
        url=SimpleNamespace(path=path),
        method=method,
        client=SimpleNamespace(host=client_host),
    )


class TestErrorHandlersLogging:
    @pytest.mark.asyncio
    async def test_http_exception_handler_does_not_log_detail_or_headers(
        self,
        error_handlers_module,
    ):
        error_handlers_module.logger = MagicMock()

        exc = HTTPException(
            status_code=400,
            detail="email=user@example.com is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
        response = await error_handlers_module.http_exception_handler(_request(), exc)

        assert response.status_code == 400
        log_kwargs = error_handlers_module.logger.warning.call_args.kwargs
        assert log_kwargs["status_code"] == 400
        assert log_kwargs["has_headers"] is True
        assert log_kwargs["response_detail_type"] == "str"
        assert "detail" not in log_kwargs
        assert "headers" not in log_kwargs

    @pytest.mark.asyncio
    async def test_base_app_exception_handler_does_not_log_detail(
        self,
        error_handlers_module,
    ):
        error_handlers_module.logger = MagicMock()

        exc = ValidationException("email=user@example.com is invalid")
        response = await error_handlers_module.base_app_exception_handler(_request(), exc)

        assert response.status_code == 400
        log_kwargs = error_handlers_module.logger.log.call_args.kwargs
        assert log_kwargs["error_code"] == "VALIDATION_ERROR"
        assert "detail" not in log_kwargs

    @pytest.mark.asyncio
    async def test_validation_exception_handler_does_not_log_input_values(
        self,
        error_handlers_module,
    ):
        error_handlers_module.logger = MagicMock()
        exc = RequestValidationError(
            [
                {
                    "type": "string_too_short",
                    "loc": ("body", "password"),
                    "msg": "String should have at least 8 characters",
                    "input": "Secret123!",
                    "ctx": {"min_length": 8, "input": "Secret123!"},
                }
            ]
        )

        response = await error_handlers_module.validation_exception_handler(_request(), exc)

        assert response.status_code == 422
        log_kwargs = error_handlers_module.logger.warning.call_args.kwargs
        assert log_kwargs["errors"] == [
            {
                "type": "string_too_short",
                "msg": "String should have at least 8 characters",
                "loc": ["body", "password"],
                "ctx": {"min_length": 8},
            }
        ]

    @pytest.mark.asyncio
    async def test_db_exception_handler_does_not_log_db_error_string(
        self,
        error_handlers_module,
    ):
        error_handlers_module.logger = MagicMock()
        exc = IntegrityError(
            "INSERT INTO users (email) VALUES (%(email)s)",
            {"email": "user@example.com"},
            Exception("duplicate key value violates unique constraint"),
        )

        response = await error_handlers_module.db_exception_handler(_request(), exc)

        assert response.status_code == 409
        log_kwargs = error_handlers_module.logger.log.call_args.kwargs
        assert log_kwargs["error_code"] == "DB_INTEGRITY_ERROR"
        assert log_kwargs["db_exception_type"] == "IntegrityError"
        assert log_kwargs["db_driver_error_type"] == "Exception"
        assert "detail" not in log_kwargs


class TestDbSessionLogging:
    @pytest.mark.asyncio
    async def test_get_db_sqlalchemy_error_logs_error_type_only(
        self,
        db_session_module,
    ):
        session = SimpleNamespace(rollback=AsyncMock())

        class SessionContext:
            async def __aenter__(self):
                return session

            async def __aexit__(self, exc_type, exc, tb):
                return False

        db_session_module.logger = MagicMock()
        db_session_module.AsyncSessionFactory = MagicMock(return_value=SessionContext())

        generator = db_session_module.get_db()
        await generator.__anext__()

        with pytest.raises(SQLAlchemyError):
            await generator.athrow(SQLAlchemyError("db error with user@example.com"))

        error_kwargs = db_session_module.logger.error.call_args_list[0].kwargs
        assert error_kwargs["error_type"] == "SQLAlchemyError"
        assert "error" not in error_kwargs
        assert "original_error" not in error_kwargs

    @pytest.mark.asyncio
    async def test_connect_db_failure_logs_error_type_only(
        self,
        db_session_module,
        monkeypatch,
    ):
        db_session_module.logger = MagicMock()
        db_session_module.engine = MagicMock()

        class ConnectContext:
            async def __aenter__(self):
                raise RuntimeError("connection failed for postgres://user:pass@host/db")

            async def __aexit__(self, exc_type, exc, tb):
                return False

        db_session_module.init_db_engine = MagicMock()
        db_session_module.engine.connect = MagicMock(return_value=ConnectContext())

        with pytest.raises(RuntimeError, match="Database connection failed"):
            await db_session_module.connect_db()

        error_kwargs = db_session_module.logger.error.call_args.kwargs
        assert error_kwargs["error_type"] == "RuntimeError"
        assert "error" not in error_kwargs


class TestDecoratorLogging:
    @pytest.mark.asyncio
    async def test_handle_auth_errors_logs_error_type_only_for_unexpected_errors(
        self,
        auth_decorators_module,
    ):
        auth_decorators_module.logger = MagicMock()

        @auth_decorators_module.handle_auth_errors("sample_login")
        async def failing_endpoint():
            raise RuntimeError("secret detail")

        with pytest.raises(HTTPException) as exc_info:
            await failing_endpoint()

        assert exc_info.value.status_code == 500
        log_kwargs = auth_decorators_module.logger.error.call_args.kwargs
        assert log_kwargs["endpoint"] == "sample_login"
        assert log_kwargs["error_type"] == "RuntimeError"
        assert "error" not in log_kwargs

    @pytest.mark.asyncio
    async def test_log_auth_event_logs_error_type_only_on_failure(
        self,
        auth_decorators_module,
    ):
        auth_decorators_module.logger = MagicMock()

        @auth_decorators_module.log_auth_event("token_refresh", user_id=1)
        async def failing_operation():
            raise RuntimeError("refresh-secret")

        with pytest.raises(RuntimeError):
            await failing_operation()

        log_kwargs = auth_decorators_module.logger.warning.call_args.kwargs
        assert log_kwargs["user_id"] == 1
        assert log_kwargs["error_type"] == "RuntimeError"
        assert "error" not in log_kwargs

    @pytest.mark.asyncio
    async def test_transactional_logs_error_type_only(
        self,
        transaction_module,
        monkeypatch,
    ):
        transaction_module.logger = MagicMock()

        class DummyAsyncSession:
            def __init__(self):
                self._in_transaction = True
                self.rollback = AsyncMock()
                self.commit = AsyncMock()

            def in_transaction(self):
                return self._in_transaction

        monkeypatch.setattr(transaction_module, "AsyncSession", DummyAsyncSession)

        @transaction_module.transactional
        async def failing_operation(db):
            raise RuntimeError("db secret")

        session = DummyAsyncSession()
        with pytest.raises(RuntimeError):
            await failing_operation(session)

        log_kwargs = transaction_module.logger.error.call_args.kwargs
        assert log_kwargs["function_name"] == "failing_operation"
        assert log_kwargs["error_type"] == "RuntimeError"
        assert "error" not in log_kwargs


class TestAdditionalErrorLogging:
    def test_security_metrics_logs_error_type_only(
        self,
        security_metrics_module,
    ):
        metrics = security_metrics_module.SecurityMetrics()
        security_metrics_module.logger = MagicMock()
        metrics._update_timestamp = MagicMock(side_effect=RuntimeError("metrics secret"))

        metrics.record_authentication_attempt(
            success=False,
            email="user@example.com",
            ip_address="192.168.1.25",
            failure_reason="invalid_credentials",
        )

        error_kwargs = security_metrics_module.logger.error.call_args.kwargs
        assert error_kwargs["error_type"] == "RuntimeError"
        assert "error" not in error_kwargs

    @pytest.mark.asyncio
    async def test_update_user_by_id_validation_logs_error_type_only(
        self,
        users_module,
    ):
        users_module.logger = MagicMock()
        current_admin = SimpleNamespace(id=10, is_superuser=True)
        user_in = SimpleNamespace(
            dict=lambda exclude_unset=False: {"full_name": "Updated"},
            model_dump=lambda exclude_unset=False: {"full_name": "Updated"},
        )
        user_service = SimpleNamespace(
            update_user=AsyncMock(
                side_effect=ValidationException("password policy violation")
            )
        )

        endpoint = inspect.unwrap(users_module.update_user_by_id)

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(
                request=_request(path="/users/5", method="PATCH"),
                user_id=5,
                user_in=user_in,
                user_service=user_service,
                db=object(),
                current_admin=current_admin,
            )

        assert exc_info.value.status_code == 400
        warning_kwargs = users_module.logger.warning.call_args.kwargs
        assert warning_kwargs["target_user_id"] == 5
        assert warning_kwargs["admin_user_id"] == 10
        assert warning_kwargs["error_type"] == "ValidationException"
        assert "error" not in warning_kwargs

    def test_extract_device_info_logs_error_type_only(
        self,
        security_module,
    ):
        class BrokenHeaders:
            def get(self, key, default=None):
                raise RuntimeError("header secret")

        request = SimpleNamespace(
            headers=BrokenHeaders(),
            client=SimpleNamespace(host="192.168.1.25"),
        )
        security_module.logger = MagicMock()

        result = security_module.extract_device_info(request)

        assert result is None
        warning_kwargs = security_module.logger.warning.call_args.kwargs
        assert warning_kwargs["error_type"] == "RuntimeError"
        assert "error" not in warning_kwargs
