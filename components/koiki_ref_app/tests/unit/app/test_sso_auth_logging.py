import importlib
import inspect
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
def sso_auth_module(logging_module):
    del logging_module
    module = importlib.import_module("app.api.v1.endpoints.sso_auth")
    return importlib.reload(module)


def _request(ip_address: str = "192.168.1.25", user_agent: str = "Mozilla/5.0"):
    return SimpleNamespace(
        client=SimpleNamespace(host=ip_address),
        headers={"user-agent": user_agent},
    )


class TestSSOAuthLogging:
    @pytest.mark.asyncio
    async def test_sso_login_success_keeps_pii_out_of_normal_logger(
        self,
        sso_auth_module,
    ):
        request = _request()
        sso_request = SimpleNamespace(
            state="signed-state",
            nonce="nonce-123",
            authorization_code="auth-code",
            code_verifier="verifier",
            redirect_uri="https://app.example.com/callback",
        )
        user_info = SimpleNamespace(email="user@example.com", sub="subject-123")
        user = SimpleNamespace(id=1, email="user@example.com")
        sso_response = SimpleNamespace(is_new_user=False)

        sso_service = SimpleNamespace(
            validate_state=MagicMock(),
            exchange_authorization_code=AsyncMock(
                return_value={
                    "id_token": "provider-id-token",
                    "access_token": "provider-access-token",
                }
            ),
            verify_id_token=AsyncMock(return_value=user_info),
            authenticate_sso_user=AsyncMock(return_value=(user, sso_response)),
            create_internal_token_pair=AsyncMock(
                return_value=("access-token", "refresh-token", 3600)
            ),
        )

        mock_logger = MagicMock()
        mock_security_logger = MagicMock()
        mock_security_metrics = MagicMock()

        sso_auth_module.logger = mock_logger
        sso_auth_module.security_logger = mock_security_logger
        sso_auth_module.security_metrics = mock_security_metrics

        endpoint = inspect.unwrap(sso_auth_module.sso_login)
        response = await endpoint(
            request=request,
            sso_request=sso_request,
            sso_service=sso_service,
            db=object(),
        )

        assert response.access_token == "access-token"
        assert response.refresh_token == "refresh-token"

        normal_log_kwargs = [call.kwargs for call in mock_logger.info.call_args_list]
        assert all("email" not in kwargs for kwargs in normal_log_kwargs)
        assert all("ip_address" not in kwargs for kwargs in normal_log_kwargs)
        assert all("device_info" not in kwargs for kwargs in normal_log_kwargs)
        assert all("sub" not in kwargs for kwargs in normal_log_kwargs)
        assert any(kwargs.get("user_id") == 1 for kwargs in normal_log_kwargs)

        mock_security_logger.log_authentication_attempt.assert_called_once()
        security_kwargs = mock_security_logger.log_authentication_attempt.call_args.kwargs
        assert security_kwargs["email"] == "user@example.com"
        assert security_kwargs["ip_address"] == "192.168.1.25"

    @pytest.mark.asyncio
    async def test_sso_login_http_error_keeps_ip_out_of_normal_warning(
        self,
        sso_auth_module,
    ):
        request = _request()
        sso_request = SimpleNamespace(
            state="signed-state",
            nonce="nonce-123",
            authorization_code="auth-code",
            code_verifier="verifier",
            redirect_uri="https://app.example.com/callback",
        )
        user_info = SimpleNamespace(email="user@example.com", sub="subject-123")

        sso_service = SimpleNamespace(
            validate_state=MagicMock(),
            exchange_authorization_code=AsyncMock(return_value={"id_token": "provider-id-token"}),
            verify_id_token=AsyncMock(return_value=user_info),
            authenticate_sso_user=AsyncMock(side_effect=HTTPException(status_code=401, detail="SSO denied")),
            create_internal_token_pair=AsyncMock(),
        )

        mock_logger = MagicMock()
        mock_security_logger = MagicMock()
        mock_security_metrics = MagicMock()

        sso_auth_module.logger = mock_logger
        sso_auth_module.security_logger = mock_security_logger
        sso_auth_module.security_metrics = mock_security_metrics

        endpoint = inspect.unwrap(sso_auth_module.sso_login)

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(
                request=request,
                sso_request=sso_request,
                sso_service=sso_service,
                db=object(),
            )

        assert exc_info.value.status_code == 401

        warning_kwargs = [call.kwargs for call in mock_logger.warning.call_args_list]
        assert warning_kwargs
        assert all("ip_address" not in kwargs for kwargs in warning_kwargs)
        assert all("email" not in kwargs for kwargs in warning_kwargs)
        assert all("sub" not in kwargs for kwargs in warning_kwargs)
        assert any(kwargs.get("status_code") == 401 for kwargs in warning_kwargs)

        mock_security_logger.log_authentication_attempt.assert_called_once()
        security_kwargs = mock_security_logger.log_authentication_attempt.call_args.kwargs
        assert security_kwargs["email"] == "user@example.com"
        assert security_kwargs["ip_address"] == "192.168.1.25"

    @pytest.mark.asyncio
    async def test_sso_login_unexpected_error_keeps_ip_out_of_normal_error(
        self,
        sso_auth_module,
    ):
        request = _request()
        sso_request = SimpleNamespace(
            state="signed-state",
            nonce="nonce-123",
            authorization_code="auth-code",
            code_verifier="verifier",
            redirect_uri="https://app.example.com/callback",
        )

        sso_service = SimpleNamespace(
            validate_state=MagicMock(side_effect=RuntimeError("unexpected failure")),
            exchange_authorization_code=AsyncMock(),
            verify_id_token=AsyncMock(),
            authenticate_sso_user=AsyncMock(),
            create_internal_token_pair=AsyncMock(),
        )

        mock_logger = MagicMock()
        mock_security_logger = MagicMock()
        mock_security_metrics = MagicMock()

        sso_auth_module.logger = mock_logger
        sso_auth_module.security_logger = mock_security_logger
        sso_auth_module.security_metrics = mock_security_metrics

        endpoint = inspect.unwrap(sso_auth_module.sso_login)

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(
                request=request,
                sso_request=sso_request,
                sso_service=sso_service,
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
    async def test_sso_health_check_jwks_failure_logs_error_type_only(
        self,
        sso_auth_module,
    ):
        request = _request()
        sso_settings = SimpleNamespace(
            validate_required_settings=MagicMock(return_value=True),
            SSO_JWKS_URI="https://issuer.example.com/.well-known/jwks.json",
            SSO_AUTO_CREATE_USERS=True,
            SSO_SIGNATURE_VALIDATION=True,
            SSO_AUTHORIZATION_ENDPOINT="https://issuer.example.com/oauth/authorize",
            SSO_SKIP_SSL_VERIFY=False,
            get_default_redirect_uri=MagicMock(
                return_value="https://app.example.com/callback"
            ),
        )

        class DummyClient:
            async def __aenter__(self):
                raise RuntimeError("jwks secret detail")

            async def __aexit__(self, exc_type, exc, tb):
                return False

        mock_logger = MagicMock()
        sso_auth_module.logger = mock_logger

        dummy_httpx = SimpleNamespace(
            AsyncClient=lambda **kwargs: DummyClient(),
            Timeout=lambda *args, **kwargs: object(),
        )

        endpoint = inspect.unwrap(sso_auth_module.sso_health_check)

        with patch.dict("sys.modules", {"httpx": dummy_httpx}):
            response = await endpoint(
                request=request,
                sso_settings=sso_settings,
            )

        assert response["jwks_accessible"] is False
        warning_kwargs = [call.kwargs for call in mock_logger.warning.call_args_list]
        assert warning_kwargs
        assert any(kwargs.get("error_type") == "RuntimeError" for kwargs in warning_kwargs)
        assert all("error" not in kwargs for kwargs in warning_kwargs)
