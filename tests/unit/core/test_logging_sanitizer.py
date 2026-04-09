import importlib
import logging
from types import SimpleNamespace

import pytest


@pytest.fixture
def logging_module(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("APP_ENV", "testing")

    config_module = importlib.import_module("libkoiki.core.config")
    importlib.reload(config_module)

    logging_module = importlib.import_module("libkoiki.core.logging")
    return importlib.reload(logging_module)


@pytest.fixture
def security_logger_module(logging_module):
    del logging_module

    security_logger_module = importlib.import_module("libkoiki.core.security_logger")
    return importlib.reload(security_logger_module)


class TestLoggingSanitizerHelpers:
    def test_get_log_field_names_excludes_sensitive_and_private_fields(self, logging_module):
        payload = {
            "email": "taro@example.com",
            "password": "secret",
            "_sa_instance_state": object(),
            "full_name": "Taro Yamada",
        }

        field_names = logging_module.get_log_field_names(payload)

        assert field_names == ["email", "full_name"]

    def test_get_log_field_names_supports_objects_and_allowlist(self, logging_module):
        payload = SimpleNamespace(
            email="taro@example.com",
            username="taro",
            hashed_password="hash-value",
            _internal="secret",
        )

        field_names = logging_module.get_log_field_names(
            payload,
            allowed_fields=["email", "username", "hashed_password"],
        )

        assert field_names == ["email", "username"]

    def test_get_error_type_name_returns_exception_class_name(self, logging_module):
        assert logging_module.get_error_type_name(RuntimeError("boom")) == "RuntimeError"

    def test_resolve_log_category_uses_logger_name_and_event_override(self, logging_module):
        assert logging_module.resolve_log_category(logger_name="audit") == logging_module.LOG_CATEGORY_AUDIT
        assert (
            logging_module.resolve_log_category(
                logger_name="app.api",
                event_dict={logging_module.INTERNAL_LOG_CATEGORY_KEY: "security"},
            )
            == logging_module.LOG_CATEGORY_SECURITY
        )
        assert logging_module.resolve_log_category(logger_name="app.api") == logging_module.LOG_CATEGORY_NORMAL

    def test_mask_email_masks_local_part(self, logging_module):
        assert logging_module.mask_email("taro@example.com") == "t***@example.com"
        assert logging_module.mask_email("ab@example.com") == "a*@example.com"

    def test_mask_ip_address_masks_ipv4_and_ipv6(self, logging_module):
        assert logging_module.mask_ip_address("192.168.1.25") == "192.168.1.xxx"
        assert (
            logging_module.mask_ip_address("2001:db8:85a3:0000:0000:8a2e:0370:7334")
            == "2001:0db8:85a3:0000:xxxx:xxxx:xxxx:xxxx"
        )

    def test_is_sensitive_key_normalizes_case_and_path(self, logging_module):
        assert logging_module.is_sensitive_key("Authorization")
        assert logging_module.is_sensitive_key("request.headers.authorization")
        assert logging_module.is_sensitive_key("client-secret")

    def test_is_sensitive_key_does_not_overmatch_state_or_session(self, logging_module):
        assert not logging_module.is_sensitive_key("state")
        assert not logging_module.is_sensitive_key("session")
        assert logging_module.is_sensitive_key("relay_state")
        assert logging_module.is_sensitive_key("session_id")

    def test_sanitize_log_value_redacts_sensitive_keys(self, logging_module):
        assert (
            logging_module.sanitize_log_value("access_token", "secret-token")
            == logging_module.REDACTED
        )
        assert (
            logging_module.sanitize_log_value("token_prefix", "secret-token-prefix")
            == logging_module.REDACTED
        )
        assert (
            logging_module.sanitize_log_value(
                "request.headers.authorization",
                "Bearer abc",
            )
            == logging_module.REDACTED
        )

    def test_sanitize_log_value_masks_normal_log_identity_fields(self, logging_module):
        assert (
            logging_module.sanitize_log_value("email", "taro@example.com")
            == "t***@example.com"
        )
        assert (
            logging_module.sanitize_log_value("ip_address", "192.168.1.25")
            == "192.168.1.xxx"
        )
        assert (
            logging_module.sanitize_log_value(
                "user_agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            )
            == "Mozilla/5.0"
        )

    def test_sanitize_log_value_keeps_identity_fields_for_audit_and_security_logs(self, logging_module):
        assert (
            logging_module.sanitize_log_value(
                "email",
                "taro@example.com",
                logger_name="audit",
            )
            == "taro@example.com"
        )
        assert (
            logging_module.sanitize_log_value(
                "ip_address",
                "192.168.1.25",
                logger_name="security",
            )
            == "192.168.1.25"
        )

    def test_sanitize_log_value_redacts_sensitive_keys_even_for_audit_and_security_logs(self, logging_module):
        assert (
            logging_module.sanitize_log_value(
                "access_token",
                "secret-token",
                logger_name="audit",
            )
            == logging_module.REDACTED
        )
        assert (
            logging_module.sanitize_log_value(
                "authorization",
                "Bearer abc",
                logger_name="security",
            )
            == logging_module.REDACTED
        )

    def test_sanitize_mapping_recursively_redacts_nested_data(self, logging_module):
        payload = {
            "email": "taro@example.com",
            "auth": {
                "access_token": "token-value",
                "profile": [
                    {"ip_address": "192.168.1.25"},
                    {"relay_state": "relay-secret"},
                ],
            },
        }

        sanitized = logging_module.sanitize_mapping(payload)

        assert sanitized["email"] == "t***@example.com"
        assert sanitized["auth"]["access_token"] == logging_module.REDACTED
        assert sanitized["auth"]["profile"][0]["ip_address"] == "192.168.1.xxx"
        assert sanitized["auth"]["profile"][1]["relay_state"] == logging_module.REDACTED
        assert payload["auth"]["access_token"] == "token-value"

    def test_sanitize_mapping_keeps_identity_fields_but_redacts_secrets_for_privileged_logs(self, logging_module):
        payload = {
            "email": "taro@example.com",
            "ip_address": "192.168.1.25",
            "refresh_token": "refresh-secret",
            "client_secret": "client-secret-value",
        }

        audit_sanitized = logging_module.sanitize_mapping(payload, logger_name="audit")
        security_sanitized = logging_module.sanitize_mapping(payload, logger_name="security")

        assert audit_sanitized["email"] == "taro@example.com"
        assert audit_sanitized["ip_address"] == "192.168.1.25"
        assert audit_sanitized["refresh_token"] == logging_module.REDACTED
        assert security_sanitized["client_secret"] == logging_module.REDACTED

    def test_sanitize_mapping_supports_internal_log_category_override(self, logging_module):
        payload = {
            logging_module.INTERNAL_LOG_CATEGORY_KEY: "audit",
            "email": "taro@example.com",
            "refresh_token": "refresh-secret",
        }

        sanitized = logging_module.sanitize_mapping(payload, logger_name="app.api")

        assert logging_module.INTERNAL_LOG_CATEGORY_KEY not in sanitized
        assert sanitized["email"] == "taro@example.com"
        assert sanitized["refresh_token"] == logging_module.REDACTED

    def test_sanitize_mapping_handles_tuple_and_set(self, logging_module):
        payload = {
            "items_tuple": (
                {"access_token": "secret-token"},
                {"email": "taro@example.com"},
            ),
            "items_set": {"alpha", "beta"},
        }

        sanitized = logging_module.sanitize_mapping(payload)

        assert isinstance(sanitized["items_tuple"], tuple)
        assert sanitized["items_tuple"][0]["access_token"] == logging_module.REDACTED
        assert sanitized["items_tuple"][1]["email"] == "t***@example.com"
        assert isinstance(sanitized["items_set"], set)
        assert sanitized["items_set"] == {"alpha", "beta"}

    def test_sanitize_mapping_handles_cycle(self, logging_module):
        payload = {}
        payload["self"] = payload

        sanitized = logging_module.sanitize_mapping(payload)

        assert sanitized["self"] == {"_sanitized": logging_module.REDACTED_CYCLE}

    def test_sanitize_mapping_applies_depth_limit(self, logging_module):
        nested = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": {
                                "level6": {
                                    "level7": "x",
                                }
                            }
                        }
                    }
                }
            }
        }

        sanitized = logging_module.sanitize_mapping(nested)

        assert sanitized["level1"]["level2"]["level3"]["level4"]["level5"]["level6"] == {
            "_sanitized": logging_module.REDACTED_DEPTH_LIMIT
        }

    def test_sanitize_log_value_preserves_non_string_scalars(self, logging_module):
        assert logging_module.sanitize_log_value("count", 3) == 3
        assert logging_module.sanitize_log_value("enabled", True) is True
        assert logging_module.sanitize_log_value("optional", None) is None


class TestLoggingSanitizerProcessor:
    class DummyLogger:
        def __init__(self, name):
            self.name = name

    def test_sanitize_event_dict_masks_normal_log_fields(self, logging_module):
        event_dict = {
            "event": "auth attempt",
            "email": "taro@example.com",
            "access_token": "secret-token",
            "profile": {"ip_address": "192.168.1.25"},
        }

        sanitized = logging_module.sanitize_event_dict(
            self.DummyLogger("app.api"),
            "info",
            event_dict,
        )

        assert sanitized["event"] == "auth attempt"
        assert sanitized["email"] == "t***@example.com"
        assert sanitized["access_token"] == logging_module.REDACTED
        assert sanitized["profile"]["ip_address"] == "192.168.1.xxx"
        assert event_dict["access_token"] == "secret-token"

    def test_sanitize_event_dict_keeps_identity_fields_for_audit_log(self, logging_module):
        event_dict = {
            "message": "audit event",
            "email": "taro@example.com",
            "ip_address": "192.168.1.25",
            "refresh_token": "refresh-secret",
        }

        sanitized = logging_module.sanitize_event_dict(
            self.DummyLogger("audit"),
            "info",
            event_dict,
        )

        assert sanitized["message"] == "audit event"
        assert sanitized["email"] == "taro@example.com"
        assert sanitized["ip_address"] == "192.168.1.25"
        assert sanitized["refresh_token"] == logging_module.REDACTED

    def test_sanitize_event_dict_supports_internal_log_category_override(self, logging_module):
        event_dict = {
            "message": "security event",
            logging_module.INTERNAL_LOG_CATEGORY_KEY: "security",
            "email": "taro@example.com",
            "access_token": "secret-token",
        }

        sanitized = logging_module.sanitize_event_dict(
            self.DummyLogger("app.api"),
            "info",
            event_dict,
        )

        assert logging_module.INTERNAL_LOG_CATEGORY_KEY not in sanitized
        assert sanitized["email"] == "taro@example.com"
        assert sanitized["access_token"] == logging_module.REDACTED

    def test_sanitize_event_dict_reduces_request_http_fields_for_normal_logs(self, logging_module):
        event_dict = {
            "message": "normal event",
            "request.http": {
                "method": "GET",
                "path": "/api/v1/auth/sso/login",
                "request_id": "req-001",
                "client": "192.168.1.25",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "authorization": "Bearer secret-token",
            },
        }

        sanitized = logging_module.sanitize_event_dict(
            self.DummyLogger("app.api"),
            "info",
            event_dict,
        )

        assert sanitized["request.http"] == {
            "method": "GET",
            "path": "/api/v1/auth/sso/login",
            "request_id": "req-001",
        }

    def test_sanitize_event_dict_keeps_request_http_identity_fields_for_audit_logs(self, logging_module):
        event_dict = {
            "message": "audit event",
            "request.http": {
                "method": "GET",
                "path": "/api/v1/auth/sso/login",
                "request_id": "req-001",
                "client": "192.168.1.25",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "authorization": "Bearer secret-token",
            },
        }

        sanitized = logging_module.sanitize_event_dict(
            self.DummyLogger("audit"),
            "info",
            event_dict,
        )

        assert sanitized["request.http"]["client"] == "192.168.1.25"
        assert sanitized["request.http"]["user_agent"] == "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        assert sanitized["request.http"]["authorization"] == logging_module.REDACTED

    def test_get_logger_emits_sanitized_output_for_normal_logger(self, logging_module, caplog):
        with caplog.at_level(logging.INFO):
            logging_module.get_logger("app.api").info(
                "login event",
                email="taro@example.com",
                access_token="secret-token",
                ip_address="192.168.1.25",
            )

        assert "secret-token" not in caplog.text
        assert "taro@example.com" not in caplog.text
        assert "192.168.1.25" not in caplog.text
        assert logging_module.REDACTED in caplog.text
        assert "t***@example.com" in caplog.text
        assert "192.168.1.xxx" in caplog.text

    def test_get_logger_emits_privileged_identity_fields_but_redacts_secrets(self, logging_module, caplog):
        with caplog.at_level(logging.INFO):
            logging_module.get_logger("audit").info(
                "audit event",
                email="taro@example.com",
                refresh_token="refresh-secret",
                ip_address="192.168.1.25",
            )

        assert "refresh-secret" not in caplog.text
        assert "taro@example.com" in caplog.text
        assert "192.168.1.25" in caplog.text
        assert logging_module.REDACTED in caplog.text

    def test_security_logger_authentication_attempt_smoke(self, security_logger_module, caplog):
        with caplog.at_level(logging.INFO):
            security_logger_module.security_logger.log_authentication_attempt(
                email="taro@example.com",
                ip_address="192.168.1.25",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                success=False,
                failure_reason="invalid_credentials",
                additional_data={"access_token": "secret-token"},
            )

        assert "secret-token" not in caplog.text
        assert "taro@example.com" in caplog.text
        assert "192.168.1.25" in caplog.text
        assert "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" in caplog.text
        assert "authentication_failed_invalid_credentials" in caplog.text

    def test_get_logger_with_request_context_smoke(self, logging_module, caplog):
        logging_module.bind_request_context(
            http={
                "request_id": "req-001",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "authorization": "Bearer secret-token",
            },
            user={"email": "taro@example.com"},
        )

        try:
            with caplog.at_level(logging.INFO):
                logging_module.get_logger("app.api").info("context event")
        finally:
            logging_module.clear_request_context()

        assert "secret-token" not in caplog.text
        assert "taro@example.com" not in caplog.text
        assert "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" not in caplog.text
        assert "req-001" in caplog.text
        assert "t***@example.com" in caplog.text
        assert "request.http" in caplog.text
