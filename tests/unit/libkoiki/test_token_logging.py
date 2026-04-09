import importlib
import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


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
def auth_service_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.services.auth_service")
    return importlib.reload(module)


@pytest.fixture
def security_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.core.security")
    return importlib.reload(module)


class TestTokenLoggingHardening:
    @pytest.mark.asyncio
    async def test_refresh_access_token_does_not_log_token_fragment(
        self,
        auth_service_module,
    ):
        auth_service = auth_service_module.AuthService(
            refresh_token_repo=AsyncMock(),
            user_repo=AsyncMock(),
        )
        auth_service_module.logger = MagicMock()
        refresh_method = inspect.unwrap(auth_service.refresh_access_token)

        with pytest.raises(auth_service_module.AuthenticationException):
            await refresh_method(
                auth_service,
                refresh_token="invalid_refresh_token",
                db=object(),
                device_info=None,
                enable_rotation=True,
            )

        debug_calls = auth_service_module.logger.debug.call_args_list
        assert debug_calls
        first_debug_call = debug_calls[0]
        assert first_debug_call.args[0] == "Refreshing access token"
        assert "token_prefix" not in first_debug_call.kwargs
        assert "refresh_token" not in first_debug_call.kwargs
        assert "invalid_refresh_token" not in str(first_debug_call)

    @pytest.mark.asyncio
    async def test_get_user_from_token_does_not_log_token_fragment(
        self,
        security_module,
    ):
        security_module.logger = MagicMock()

        with patch.object(
            security_module.jwt,
            "decode",
            side_effect=security_module.InvalidTokenError("token format mismatch"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await security_module.get_user_from_token("header.payload.signature")

        assert exc_info.value.status_code == 401
        warning_call = security_module.logger.warning.call_args
        assert warning_call.args[0] == "Token validation failed"
        assert warning_call.kwargs["error_type"] == "InvalidTokenError"
        assert "token" not in warning_call.kwargs
        assert "header.payload.signature" not in str(warning_call)
