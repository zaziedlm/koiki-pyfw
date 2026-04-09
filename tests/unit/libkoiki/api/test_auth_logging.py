import importlib
import inspect
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException


@pytest.fixture
def logging_module(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("APP_ENV", "testing")

    config_module = importlib.import_module("libkoiki.core.config")
    importlib.reload(config_module)

    logging_module = importlib.import_module("libkoiki.core.logging")
    logging_module = importlib.reload(logging_module)
    logging_module.setup_logging()
    return logging_module


@pytest.fixture
def auth_password_module(logging_module):
    del logging_module
    module = importlib.import_module("libkoiki.api.v1.endpoints.auth_password")
    return importlib.reload(module)


@pytest.fixture
def auth_basic_module(logging_module):
    del logging_module
    module = importlib.import_module("libkoiki.api.v1.endpoints.auth_basic")
    return importlib.reload(module)


@pytest.fixture
def auth_token_module(logging_module):
    del logging_module
    module = importlib.import_module("libkoiki.api.v1.endpoints.auth_token")
    return importlib.reload(module)


def _request(ip_address: str = "192.168.1.25", user_agent: str = "Mozilla/5.0"):
    return SimpleNamespace(
        client=SimpleNamespace(host=ip_address),
        headers={"user-agent": user_agent},
    )


class TestAuthPasswordLogging:
    @pytest.mark.asyncio
    async def test_request_password_reset_does_not_log_reset_token_or_email(
        self,
        auth_password_module,
    ):
        request = _request()
        reset_data = SimpleNamespace(email="reset@example.com")
        user = SimpleNamespace(id=1, email="reset@example.com", is_active=True)
        token_model = SimpleNamespace(
            expires_at=datetime(2026, 4, 9, tzinfo=timezone.utc),
        )

        user_service = SimpleNamespace(
            get_user_by_email=AsyncMock(return_value=user),
        )
        password_reset_service = SimpleNamespace(
            create_reset_token=AsyncMock(return_value=("secret-reset-token", token_model)),
        )
        mock_logger = MagicMock()

        auth_password_module.logger = mock_logger
        auth_password_module.security_logger = MagicMock()
        endpoint = inspect.unwrap(auth_password_module.request_password_reset)

        await endpoint(
            request=request,
            reset_data=reset_data,
            user_service=user_service,
            password_reset_service=password_reset_service,
            db=object(),
        )

        logged_kwargs = [
            kwargs
            for _, kwargs in [call for call in mock_logger.info.call_args_list]
        ]

        assert all("reset_token" not in kwargs for kwargs in logged_kwargs)
        assert all("email" not in kwargs for kwargs in logged_kwargs)
        assert all("token" not in kwargs for kwargs in logged_kwargs)
        assert any(kwargs.get("user_id") == 1 for kwargs in logged_kwargs)
        security_call = auth_password_module.security_logger.log_security_event.call_args
        assert (
            security_call.args[0]
            == auth_password_module.SECURITY_EVENT_PASSWORD_RESET_REQUESTED_EXISTING_USER
        )
        security_kwargs = security_call.kwargs
        assert security_kwargs["email"] == "reset@example.com"
        assert security_kwargs["auth_method"] == "password_reset"

    @pytest.mark.asyncio
    async def test_confirm_password_reset_does_not_log_token_fragment(
        self,
        auth_password_module,
    ):
        request = _request()
        reset_data = SimpleNamespace(
            token="secret-reset-token-value",
            new_password="NewPass123!",
        )
        user = SimpleNamespace(id=1, email="reset@example.com")
        user_service = SimpleNamespace(update_user=AsyncMock())
        password_reset_service = SimpleNamespace(
            complete_password_reset=AsyncMock(return_value=user),
            revoke_user_tokens=AsyncMock(),
        )
        mock_logger = MagicMock()

        auth_password_module.logger = mock_logger
        auth_password_module.security_logger = MagicMock()
        endpoint = inspect.unwrap(auth_password_module.confirm_password_reset)

        await endpoint(
            request=request,
            reset_data=reset_data,
            user_service=user_service,
            password_reset_service=password_reset_service,
            db=object(),
        )

        messages = [call.args[0] for call in mock_logger.info.call_args_list]
        logged_kwargs = [call.kwargs for call in mock_logger.info.call_args_list]

        assert "Password reset confirmation attempt" in messages
        assert all("token" not in kwargs for kwargs in logged_kwargs)
        assert all("email" not in kwargs for kwargs in logged_kwargs)
        assert all("secret-reset-token-value" not in str(call) for call in mock_logger.info.call_args_list)
        security_call = auth_password_module.security_logger.log_security_event.call_args
        assert (
            security_call.args[0]
            == auth_password_module.SECURITY_EVENT_PASSWORD_RESET_COMPLETED
        )
        security_kwargs = security_call.kwargs
        assert security_kwargs["user_id"] == 1
        assert security_kwargs["auth_method"] == "password_reset"

    @pytest.mark.asyncio
    async def test_confirm_password_reset_invalid_token_emits_security_event(
        self,
        auth_password_module,
    ):
        request = _request()
        reset_data = SimpleNamespace(
            token="secret-reset-token-value",
            new_password="NewPass123!",
        )
        user_service = SimpleNamespace(update_user=AsyncMock())
        password_reset_service = SimpleNamespace(
            complete_password_reset=AsyncMock(
                side_effect=auth_password_module.ValidationException(
                    "Invalid or expired password reset token"
                )
            ),
            revoke_user_tokens=AsyncMock(),
        )
        auth_password_module.logger = MagicMock()
        auth_password_module.security_logger = MagicMock()
        endpoint = inspect.unwrap(auth_password_module.confirm_password_reset)

        with pytest.raises(auth_password_module.ValidationException):
            await endpoint(
                request=request,
                reset_data=reset_data,
                user_service=user_service,
                password_reset_service=password_reset_service,
                db=object(),
            )

        security_call = auth_password_module.security_logger.log_security_event.call_args
        assert (
            security_call.args[0]
            == auth_password_module.SECURITY_EVENT_PASSWORD_RESET_REJECTED_INVALID_TOKEN
        )
        security_kwargs = security_call.kwargs
        assert security_kwargs["failure_reason"] == "Invalid or expired password reset token"
        assert security_kwargs["auth_method"] == "password_reset"


class TestAuthBasicLogging:
    @pytest.mark.asyncio
    async def test_login_invalid_credentials_keeps_email_and_ip_out_of_normal_logger(
        self,
        auth_basic_module,
    ):
        form_data = SimpleNamespace(
            username="login@example.com",
            password="wrong-password",
        )
        request = _request()
        user_service = SimpleNamespace(
            authenticate_user=AsyncMock(return_value=None),
        )
        auth_service = SimpleNamespace()
        login_security_service = SimpleNamespace(
            check_login_allowed=AsyncMock(return_value=(True, None, None)),
            apply_progressive_delay=AsyncMock(),
            record_login_attempt=AsyncMock(),
        )
        security_logger = MagicMock()
        security_metrics = MagicMock()
        mock_logger = MagicMock()

        auth_basic_module.logger = mock_logger
        auth_basic_module.security_logger = security_logger
        auth_basic_module.security_metrics = security_metrics
        endpoint = inspect.unwrap(auth_basic_module.login_for_access_token)

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(
                request=request,
                form_data=form_data,
                user_service=user_service,
                auth_service=auth_service,
                login_security_service=login_security_service,
                db=object(),
            )

        assert exc_info.value.status_code == 401

        normal_log_kwargs = [call.kwargs for call in mock_logger.info.call_args_list + mock_logger.warning.call_args_list]
        assert all("email" not in kwargs for kwargs in normal_log_kwargs)
        assert all("ip_address" not in kwargs for kwargs in normal_log_kwargs)
        security_kwargs = security_logger.log_authentication_attempt.call_args.kwargs
        assert security_kwargs["failure_reason"] == "invalid_credentials"
        assert security_kwargs["additional_data"]["auth_method"] == "password"

    @pytest.mark.asyncio
    async def test_login_inactive_user_emits_security_event_with_password_auth_method(
        self,
        auth_basic_module,
    ):
        form_data = SimpleNamespace(
            username="login@example.com",
            password="right-password",
        )
        request = _request()
        inactive_user = SimpleNamespace(id=22, is_active=False)
        user_service = SimpleNamespace(
            authenticate_user=AsyncMock(return_value=inactive_user),
        )
        auth_service = SimpleNamespace()
        login_security_service = SimpleNamespace(
            check_login_allowed=AsyncMock(return_value=(True, None, None)),
            apply_progressive_delay=AsyncMock(),
            record_login_attempt=AsyncMock(),
        )
        security_logger = MagicMock()
        security_metrics = MagicMock()
        mock_logger = MagicMock()

        auth_basic_module.logger = mock_logger
        auth_basic_module.security_logger = security_logger
        auth_basic_module.security_metrics = security_metrics
        endpoint = inspect.unwrap(auth_basic_module.login_for_access_token)

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(
                request=request,
                form_data=form_data,
                user_service=user_service,
                auth_service=auth_service,
                login_security_service=login_security_service,
                db=object(),
            )

        assert exc_info.value.status_code == 400
        security_kwargs = security_logger.log_authentication_attempt.call_args.kwargs
        assert security_kwargs["failure_reason"] == "inactive_user"
        assert security_kwargs["user_id"] == 22
        assert security_kwargs["additional_data"]["auth_method"] == "password"

    @pytest.mark.asyncio
    async def test_registration_and_logout_keep_email_out_of_normal_logger(
        self,
        auth_basic_module,
    ):
        new_user = SimpleNamespace(
            id=10,
            email="registered@example.com",
            full_name="Registered User",
            is_active=True,
            created_at=datetime(2026, 4, 9, tzinfo=timezone.utc),
        )
        user_service = SimpleNamespace(create_user=AsyncMock(return_value=new_user))
        register_logger = MagicMock()
        auth_basic_module.logger = register_logger

        register_endpoint = inspect.unwrap(auth_basic_module.register)
        register_response = await register_endpoint(
            request=_request(),
            user_in=SimpleNamespace(
                email="registered@example.com",
                password="StrongPass123!",
                full_name="Registered User",
            ),
            user_service=user_service,
            db=object(),
        )

        assert register_response.message == "User registered successfully"
        register_kwargs = [call.kwargs for call in register_logger.info.call_args_list]
        assert all("email" not in kwargs for kwargs in register_kwargs)

        logout_logger = MagicMock()
        auth_basic_module.logger = logout_logger
        logout_endpoint = inspect.unwrap(auth_basic_module.logout)
        logout_response = await logout_endpoint(
            current_user=SimpleNamespace(id=10, email="registered@example.com"),
        )

        assert logout_response.message == "Successfully logged out"
        logout_kwargs = [call.kwargs for call in logout_logger.info.call_args_list]
        assert all("email" not in kwargs for kwargs in logout_kwargs)


class TestAuthTokenLogging:
    @pytest.mark.asyncio
    async def test_refresh_token_rejection_emits_security_event(
        self,
        auth_token_module,
    ):
        request = _request()
        refresh_data = SimpleNamespace(refresh_token="invalid-refresh-token")
        auth_service = SimpleNamespace(
            refresh_access_token=AsyncMock(
                side_effect=auth_token_module.AuthenticationException(
                    "Invalid refresh token format"
                )
            )
        )
        auth_token_module.logger = MagicMock()
        auth_token_module.security_logger = MagicMock()
        endpoint = inspect.unwrap(auth_token_module.refresh_token)

        with pytest.raises(auth_token_module.AuthenticationException):
            await endpoint(
                request=request,
                refresh_data=refresh_data,
                auth_service=auth_service,
                db=object(),
            )

        security_call = auth_token_module.security_logger.log_security_event.call_args
        assert (
            security_call.args[0]
            == auth_token_module.SECURITY_EVENT_REFRESH_TOKEN_REJECTED
        )
        security_kwargs = security_call.kwargs
        assert security_kwargs["auth_method"] == "refresh_token"
        assert security_kwargs["failure_reason"] == "Invalid refresh token format"
        assert security_kwargs["endpoint"] == "/refresh"
