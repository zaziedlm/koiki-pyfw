import importlib
import inspect
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

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
def saml_auth_module(logging_module):
    del logging_module
    module = importlib.import_module("app.api.v1.endpoints.saml_auth")
    return importlib.reload(module)


def _request(
    ip_address: str = "192.168.1.25",
    user_agent: str = "Mozilla/5.0",
    method: str = "GET",
):
    return SimpleNamespace(
        client=SimpleNamespace(host=ip_address),
        headers={"user-agent": user_agent},
        method=method,
    )


class TestSAMLAuthLogging:
    @pytest.mark.asyncio
    async def test_saml_acs_success_keeps_protocol_values_out_of_normal_logger(
        self,
        saml_auth_module,
    ):
        request = _request()
        ticket_expires = datetime.now(timezone.utc) + timedelta(minutes=5)
        user = SimpleNamespace(id=10)
        user_info = SimpleNamespace(subject_id="subject-123")

        saml_service = SimpleNamespace(
            handle_acs_request=AsyncMock(
                return_value=(
                    "https://app.example.com/callback",
                    "login-ticket",
                    ticket_expires,
                    user_info,
                    user,
                )
            ),
            build_login_redirect_url=MagicMock(
                return_value="https://app.example.com/callback?ticket=opaque"
            ),
        )

        mock_logger = MagicMock()
        saml_auth_module.logger = mock_logger

        endpoint = inspect.unwrap(saml_auth_module.saml_acs)
        response = await endpoint(
            request=request,
            saml_service=saml_service,
            db=object(),
            saml_response="encoded-response",
            relay_state="signed-relay-state",
        )

        assert response.status_code == 303
        log_kwargs = mock_logger.info.call_args.kwargs
        assert log_kwargs["user_id"] == 10
        assert "redirect_uri" not in log_kwargs
        assert "subject_id" not in log_kwargs
        assert "ticket_expires" not in log_kwargs

    @pytest.mark.asyncio
    async def test_saml_acs_unexpected_error_logs_error_type_only(
        self,
        saml_auth_module,
    ):
        request = _request()
        saml_service = SimpleNamespace(
            handle_acs_request=AsyncMock(side_effect=RuntimeError("acs secret detail")),
        )

        mock_logger = MagicMock()
        saml_auth_module.logger = mock_logger

        endpoint = inspect.unwrap(saml_auth_module.saml_acs)

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(
                request=request,
                saml_service=saml_service,
                db=object(),
                saml_response="encoded-response",
                relay_state="signed-relay-state",
            )

        assert exc_info.value.status_code == 500
        error_kwargs = mock_logger.error.call_args.kwargs
        assert error_kwargs["error_type"] == "RuntimeError"
        assert "error" not in error_kwargs

    @pytest.mark.asyncio
    async def test_saml_login_success_keeps_pii_out_of_normal_logger(
        self,
        saml_auth_module,
    ):
        request = _request()
        login_request = SimpleNamespace(
            login_ticket="signed-ticket",
            relay_state="signed-relay-state",
        )
        user = SimpleNamespace(id=1, email="user@example.com")

        saml_service = SimpleNamespace(
            exchange_login_ticket=AsyncMock(
                return_value=(user, "access-token", "refresh-token", 3600)
            )
        )

        mock_logger = MagicMock()
        mock_security_logger = MagicMock()
        mock_security_metrics = MagicMock()

        saml_auth_module.logger = mock_logger
        saml_auth_module.security_logger = mock_security_logger
        saml_auth_module.security_metrics = mock_security_metrics

        endpoint = inspect.unwrap(saml_auth_module.saml_login)
        response = await endpoint(
            request=request,
            login_request=login_request,
            saml_service=saml_service,
            db=object(),
        )

        assert response.access_token == "access-token"
        assert response.refresh_token == "refresh-token"

        normal_log_kwargs = [call.kwargs for call in mock_logger.info.call_args_list]
        assert all("email" not in kwargs for kwargs in normal_log_kwargs)
        assert all("ip_address" not in kwargs for kwargs in normal_log_kwargs)
        assert all("device_info" not in kwargs for kwargs in normal_log_kwargs)
        assert any(kwargs.get("user_id") == 1 for kwargs in normal_log_kwargs)

        mock_security_logger.log_authentication_attempt.assert_called_once()
        security_kwargs = mock_security_logger.log_authentication_attempt.call_args.kwargs
        assert security_kwargs["email"] == "user@example.com"
        assert security_kwargs["ip_address"] == "192.168.1.25"

    @pytest.mark.asyncio
    async def test_saml_login_http_error_keeps_ip_out_of_normal_warning(
        self,
        saml_auth_module,
    ):
        request = _request()
        login_request = SimpleNamespace(
            login_ticket="signed-ticket",
            relay_state="signed-relay-state",
        )

        saml_service = SimpleNamespace(
            exchange_login_ticket=AsyncMock(
                side_effect=HTTPException(status_code=401, detail="SAML denied")
            )
        )

        mock_logger = MagicMock()
        mock_security_logger = MagicMock()
        mock_security_metrics = MagicMock()

        saml_auth_module.logger = mock_logger
        saml_auth_module.security_logger = mock_security_logger
        saml_auth_module.security_metrics = mock_security_metrics

        endpoint = inspect.unwrap(saml_auth_module.saml_login)

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(
                request=request,
                login_request=login_request,
                saml_service=saml_service,
                db=object(),
            )

        assert exc_info.value.status_code == 401

        warning_kwargs = [call.kwargs for call in mock_logger.warning.call_args_list]
        assert warning_kwargs
        assert all("ip_address" not in kwargs for kwargs in warning_kwargs)
        assert all("email" not in kwargs for kwargs in warning_kwargs)
        assert any(kwargs.get("status_code") == 401 for kwargs in warning_kwargs)

        mock_security_logger.log_authentication_attempt.assert_called_once()
        security_kwargs = mock_security_logger.log_authentication_attempt.call_args.kwargs
        assert security_kwargs["email"] == "unknown"
        assert security_kwargs["ip_address"] == "192.168.1.25"

    @pytest.mark.asyncio
    async def test_saml_login_unexpected_error_keeps_ip_out_of_normal_error(
        self,
        saml_auth_module,
    ):
        request = _request()
        login_request = SimpleNamespace(
            login_ticket="signed-ticket",
            relay_state="signed-relay-state",
        )

        saml_service = SimpleNamespace(
            exchange_login_ticket=AsyncMock(side_effect=RuntimeError("unexpected failure"))
        )

        mock_logger = MagicMock()
        mock_security_logger = MagicMock()
        mock_security_metrics = MagicMock()

        saml_auth_module.logger = mock_logger
        saml_auth_module.security_logger = mock_security_logger
        saml_auth_module.security_metrics = mock_security_metrics

        endpoint = inspect.unwrap(saml_auth_module.saml_login)

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(
                request=request,
                login_request=login_request,
                saml_service=saml_service,
                db=object(),
            )

        assert exc_info.value.status_code == 500

        error_kwargs = [call.kwargs for call in mock_logger.error.call_args_list]
        assert error_kwargs
        assert all("ip_address" not in kwargs for kwargs in error_kwargs)
        assert all("email" not in kwargs for kwargs in error_kwargs)
        assert all(kwargs.get("error_type") == "RuntimeError" for kwargs in error_kwargs)
        assert all("error" not in kwargs for kwargs in error_kwargs)

        mock_security_logger.log_authentication_attempt.assert_called_once()
        security_kwargs = mock_security_logger.log_authentication_attempt.call_args.kwargs
        assert security_kwargs["email"] == "unknown"
        assert security_kwargs["ip_address"] == "192.168.1.25"

    @pytest.mark.asyncio
    async def test_saml_user_info_keeps_subject_out_of_normal_logger(
        self,
        saml_auth_module,
    ):
        request = _request()
        current_user = SimpleNamespace(id=5)
        saml_response = SimpleNamespace(user_info=SimpleNamespace(subject_id="subject-123"))
        saml_service = SimpleNamespace(
            get_user_saml_info=AsyncMock(return_value=saml_response)
        )

        mock_logger = MagicMock()
        saml_auth_module.logger = mock_logger

        endpoint = inspect.unwrap(saml_auth_module.get_saml_user_info)
        response = await endpoint(
            request=request,
            current_user=current_user,
            db=object(),
            saml_service=saml_service,
        )

        assert response is saml_response
        log_kwargs = mock_logger.info.call_args.kwargs
        assert log_kwargs["user_id"] == 5
        assert "saml_subject_id" not in log_kwargs

    @pytest.mark.asyncio
    async def test_saml_user_info_unexpected_error_logs_error_type_only(
        self,
        saml_auth_module,
    ):
        request = _request()
        current_user = SimpleNamespace(id=5)
        saml_service = SimpleNamespace(
            get_user_saml_info=AsyncMock(side_effect=RuntimeError("user info secret"))
        )

        mock_logger = MagicMock()
        saml_auth_module.logger = mock_logger

        endpoint = inspect.unwrap(saml_auth_module.get_saml_user_info)

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(
                request=request,
                current_user=current_user,
                db=object(),
                saml_service=saml_service,
            )

        assert exc_info.value.status_code == 500
        error_kwargs = mock_logger.error.call_args.kwargs
        assert error_kwargs["user_id"] == 5
        assert error_kwargs["error_type"] == "RuntimeError"
        assert "error" not in error_kwargs

    @pytest.mark.asyncio
    async def test_saml_logout_and_sls_keep_redirects_out_of_normal_logger(
        self,
        saml_auth_module,
    ):
        current_user = SimpleNamespace(id=7)
        logout_request = _request()
        sls_request = _request(method="GET")

        saml_service = SimpleNamespace(
            initiate_logout=AsyncMock(return_value="https://idp.example.com/logout"),
            process_logout_request=AsyncMock(
                return_value="https://app.example.com/post-logout"
            ),
        )

        mock_logger = MagicMock()
        saml_auth_module.logger = mock_logger

        logout_endpoint = inspect.unwrap(saml_auth_module.saml_logout)
        logout_response = await logout_endpoint(
            request=logout_request,
            current_user=current_user,
            saml_service=saml_service,
            db=object(),
            redirect_uri="https://app.example.com/post-logout",
        )

        sls_endpoint = inspect.unwrap(saml_auth_module.saml_single_logout_service)
        sls_response = await sls_endpoint(
            request=sls_request,
            saml_service=saml_service,
            db=object(),
        )

        assert logout_response.status_code == 303
        assert sls_response.status_code == 303

        logout_kwargs = mock_logger.info.call_args_list[0].kwargs
        assert logout_kwargs["user_id"] == 7
        assert "redirect" not in logout_kwargs

        sls_kwargs = mock_logger.info.call_args_list[1].kwargs
        assert "redirect" not in sls_kwargs

    @pytest.mark.asyncio
    async def test_saml_health_check_failure_logs_error_type_only(
        self,
        saml_auth_module,
    ):
        request = _request()
        saml_service = SimpleNamespace(
            saml_settings=SimpleNamespace(
                validate_required_settings=MagicMock(
                    side_effect=RuntimeError("health secret detail")
                ),
                SAML_IDP_METADATA_URL=None,
            )
        )

        mock_logger = MagicMock()
        saml_auth_module.logger = mock_logger

        endpoint = inspect.unwrap(saml_auth_module.saml_health_check)

        response = await endpoint(
            request=request,
            saml_service=saml_service,
        )

        assert response.status == "error"
        error_kwargs = mock_logger.error.call_args.kwargs
        assert error_kwargs["error_type"] == "RuntimeError"
        assert "error" not in error_kwargs
