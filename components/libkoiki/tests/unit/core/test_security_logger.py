import importlib
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def security_logger_module(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("APP_ENV", "testing")

    config_module = importlib.import_module("libkoiki.core.config")
    importlib.reload(config_module)

    logging_module = importlib.import_module("libkoiki.core.logging")
    importlib.reload(logging_module)

    module = importlib.import_module("libkoiki.core.security_logger")
    return importlib.reload(module)


class TestSecurityLogger:
    def test_password_login_failure_maps_to_allowed_event(self, security_logger_module):
        mock_logger = MagicMock()
        security_logger = security_logger_module.SecurityLogger()
        security_logger.security_logger = mock_logger

        security_logger.log_authentication_attempt(
            email="user@example.com",
            ip_address="192.168.1.25",
            user_agent="Mozilla/5.0",
            success=False,
            failure_reason="invalid_credentials",
            additional_data={"auth_method": "password", "access_token": "secret-token"},
        )

        kwargs = mock_logger.warning.call_args.kwargs
        assert kwargs["event_type"] == (
            security_logger_module.SECURITY_EVENT_AUTHENTICATION_FAILED_INVALID_CREDENTIALS
        )
        assert kwargs["auth_method"] == "password"
        assert kwargs["email"] == "user@example.com"
        assert kwargs["failure_reason"] == "invalid_credentials"
        assert "access_token" not in kwargs

    def test_inactive_user_failure_maps_to_inactive_event(self, security_logger_module):
        mock_logger = MagicMock()
        security_logger = security_logger_module.SecurityLogger()
        security_logger.security_logger = mock_logger

        security_logger.log_authentication_attempt(
            email="user@example.com",
            ip_address="192.168.1.25",
            success=False,
            failure_reason="inactive_user",
            user_id=7,
            additional_data={"auth_method": "password"},
        )

        kwargs = mock_logger.warning.call_args.kwargs
        assert (
            kwargs["event_type"]
            == security_logger_module.SECURITY_EVENT_AUTHENTICATION_FAILED_INACTIVE_USER
        )
        assert kwargs["user_id"] == 7

    def test_password_login_success_maps_to_risk_checked_event(self, security_logger_module):
        mock_logger = MagicMock()
        security_logger = security_logger_module.SecurityLogger()
        security_logger.security_logger = mock_logger

        security_logger.log_authentication_attempt(
            email="user@example.com",
            ip_address="192.168.1.25",
            success=True,
            user_id=9,
            additional_data={"auth_method": "password", "request_id": "req-001"},
        )

        kwargs = mock_logger.info.call_args.kwargs
        assert (
            kwargs["event_type"]
            == security_logger_module.SECURITY_EVENT_AUTHENTICATION_SUCCEEDED_AFTER_RISK_CHECK
        )
        assert kwargs["request_id"] == "req-001"

    def test_sso_and_saml_authentication_events_map_to_provider_specific_types(
        self,
        security_logger_module,
    ):
        mock_logger = MagicMock()
        security_logger = security_logger_module.SecurityLogger()
        security_logger.security_logger = mock_logger

        security_logger.log_authentication_attempt(
            email="user@example.com",
            ip_address="192.168.1.25",
            success=True,
            additional_data={"auth_method": "sso"},
        )
        first_kwargs = mock_logger.info.call_args.kwargs
        assert first_kwargs["event_type"] == security_logger_module.SECURITY_EVENT_SSO_LOGIN_SUCCEEDED

        security_logger.log_authentication_attempt(
            email="user@example.com",
            ip_address="192.168.1.25",
            success=False,
            failure_reason="saml_verification_failed",
            additional_data={"auth_method": "saml", "subject_id": "subject-123"},
        )
        second_kwargs = mock_logger.warning.call_args.kwargs
        assert second_kwargs["event_type"] == security_logger_module.SECURITY_EVENT_SAML_LOGIN_FAILED
        assert second_kwargs["subject_id"] == "subject-123"

    def test_account_lockout_and_rate_limit_use_allowed_event_types(self, security_logger_module):
        mock_logger = MagicMock()
        security_logger = security_logger_module.SecurityLogger()
        security_logger.security_logger = mock_logger

        security_logger.log_account_lockout(
            email="user@example.com",
            ip_address="192.168.1.25",
            lockout_type="security_policy",
            attempt_count=4,
            lockout_duration=300,
            additional_data={
                "auth_method": "password",
                "failure_reason": "too_many_attempts",
                "unexpected_field": "drop-me",
            },
        )
        lockout_kwargs = mock_logger.warning.call_args.kwargs
        assert (
            lockout_kwargs["event_type"]
            == security_logger_module.SECURITY_EVENT_AUTHENTICATION_BLOCKED_LOCKOUT
        )
        assert lockout_kwargs["count"] == 4
        assert lockout_kwargs["lockout_duration"] == 300
        assert "unexpected_field" not in lockout_kwargs

        security_logger.log_rate_limit_exceeded(
            endpoint="/api/v1/auth/login",
            ip_address="192.168.1.25",
            user_id=3,
            limit_type="login",
            additional_data={"auth_method": "password"},
        )
        rate_limit_kwargs = mock_logger.warning.call_args.kwargs
        assert (
            rate_limit_kwargs["event_type"]
            == security_logger_module.SECURITY_EVENT_RATE_LIMIT_EXCEEDED_SECURITY_SENSITIVE_ENDPOINT
        )
        assert rate_limit_kwargs["endpoint"] == "/api/v1/auth/login"
        assert rate_limit_kwargs["failure_reason"] == "login"

    def test_log_security_event_rejects_unsupported_event_type(self, security_logger_module):
        security_logger = security_logger_module.SecurityLogger()

        with pytest.raises(ValueError):
            security_logger.log_security_event("non_policy_event", severity="warning")
