"""
セキュリティイベント専用ロガー。

許可された限定イベントだけを security logger へ流し、項目粒度も共通化する。
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import structlog

SECURITY_EVENT_AUTHENTICATION_FAILED_INVALID_CREDENTIALS = (
    "authentication_failed_invalid_credentials"
)
SECURITY_EVENT_AUTHENTICATION_FAILED_INACTIVE_USER = (
    "authentication_failed_inactive_user"
)
SECURITY_EVENT_AUTHENTICATION_BLOCKED_LOCKOUT = (
    "authentication_blocked_lockout"
)
SECURITY_EVENT_AUTHENTICATION_SUCCEEDED_AFTER_RISK_CHECK = (
    "authentication_succeeded_after_risk_check"
)
# Security event names are log labels, not secrets.
SECURITY_EVENT_REFRESH_TOKEN_REJECTED = "refresh_token_rejected"  # nosec B105
SECURITY_EVENT_PASSWORD_RESET_REQUESTED_EXISTING_USER = (
    # Security event names are log labels, not secrets.
    "password_reset_requested_existing_user"  # nosec B105
)
# Security event names are log labels, not secrets.
SECURITY_EVENT_PASSWORD_RESET_COMPLETED = "password_reset_completed"  # nosec B105
SECURITY_EVENT_PASSWORD_RESET_REJECTED_INVALID_TOKEN = (
    # Security event names are log labels, not secrets.
    "password_reset_rejected_invalid_token"  # nosec B105
)
SECURITY_EVENT_SSO_LOGIN_FAILED = "sso_login_failed"
SECURITY_EVENT_SSO_LOGIN_SUCCEEDED = "sso_login_succeeded"
SECURITY_EVENT_SAML_LOGIN_FAILED = "saml_login_failed"
SECURITY_EVENT_SAML_LOGIN_SUCCEEDED = "saml_login_succeeded"
SECURITY_EVENT_TOKEN_REUSE_OR_INTEGRITY_VIOLATION_DETECTED = (
    # Security event names are log labels, not secrets.
    "token_reuse_or_integrity_violation_detected"  # nosec B105
)
SECURITY_EVENT_SUSPICIOUS_ACTIVITY_DETECTED = "suspicious_activity_detected"
SECURITY_EVENT_RATE_LIMIT_EXCEEDED_SECURITY_SENSITIVE_ENDPOINT = (
    "rate_limit_exceeded_security_sensitive_endpoint"
)

ALLOWED_SECURITY_EVENT_TYPES = {
    SECURITY_EVENT_AUTHENTICATION_FAILED_INVALID_CREDENTIALS,
    SECURITY_EVENT_AUTHENTICATION_FAILED_INACTIVE_USER,
    SECURITY_EVENT_AUTHENTICATION_BLOCKED_LOCKOUT,
    SECURITY_EVENT_AUTHENTICATION_SUCCEEDED_AFTER_RISK_CHECK,
    SECURITY_EVENT_REFRESH_TOKEN_REJECTED,
    SECURITY_EVENT_PASSWORD_RESET_REQUESTED_EXISTING_USER,
    SECURITY_EVENT_PASSWORD_RESET_COMPLETED,
    SECURITY_EVENT_PASSWORD_RESET_REJECTED_INVALID_TOKEN,
    SECURITY_EVENT_SSO_LOGIN_FAILED,
    SECURITY_EVENT_SSO_LOGIN_SUCCEEDED,
    SECURITY_EVENT_SAML_LOGIN_FAILED,
    SECURITY_EVENT_SAML_LOGIN_SUCCEEDED,
    SECURITY_EVENT_TOKEN_REUSE_OR_INTEGRITY_VIOLATION_DETECTED,
    SECURITY_EVENT_SUSPICIOUS_ACTIVITY_DETECTED,
    SECURITY_EVENT_RATE_LIMIT_EXCEEDED_SECURITY_SENSITIVE_ENDPOINT,
}

ALLOWED_SECURITY_FIELDS = {
    "event_type",
    "timestamp",
    "request_id",
    "user_id",
    "username",
    "email",
    "ip_address",
    "user_agent",
    "endpoint",
    "auth_method",
    "failure_reason",
    "lockout_duration",
    "count",
    "threshold",
    "sso_provider",
    "saml_provider",
    "subject_id",
}


class SecurityLogger:
    """セキュリティイベント専用ロガー"""

    def __init__(self):
        self.security_logger = structlog.get_logger("security")

    def _pick_log_method(self, severity: str):
        normalized = severity.lower()
        return getattr(self.security_logger, normalized, self.security_logger.info)

    def _build_base_event_data(self, event_type: str, **kwargs: Any) -> Dict[str, Any]:
        if event_type not in ALLOWED_SECURITY_EVENT_TYPES:
            raise ValueError(f"Unsupported security event type: {event_type}")

        event_data: Dict[str, Any] = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        event_data.update(kwargs)

        filtered: Dict[str, Any] = {}
        for key, value in event_data.items():
            if key not in ALLOWED_SECURITY_FIELDS:
                continue
            if value is None:
                continue
            filtered[key] = value

        return filtered

    def _extract_auth_method(
        self,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if not additional_data:
            return None
        auth_method = additional_data.get("auth_method")
        if isinstance(auth_method, str):
            return auth_method
        return None

    def _authentication_event_type(
        self,
        *,
        success: bool,
        failure_reason: Optional[str],
        auth_method: Optional[str],
    ) -> str:
        normalized_method = auth_method.lower() if isinstance(auth_method, str) else None

        if normalized_method == "sso":
            return (
                SECURITY_EVENT_SSO_LOGIN_SUCCEEDED
                if success
                else SECURITY_EVENT_SSO_LOGIN_FAILED
            )

        if normalized_method == "saml":
            return (
                SECURITY_EVENT_SAML_LOGIN_SUCCEEDED
                if success
                else SECURITY_EVENT_SAML_LOGIN_FAILED
            )

        if success:
            return SECURITY_EVENT_AUTHENTICATION_SUCCEEDED_AFTER_RISK_CHECK

        if failure_reason == "inactive_user":
            return SECURITY_EVENT_AUTHENTICATION_FAILED_INACTIVE_USER

        return SECURITY_EVENT_AUTHENTICATION_FAILED_INVALID_CREDENTIALS

    def log_authentication_attempt(
        self,
        email: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        success: bool = False,
        failure_reason: Optional[str] = None,
        user_id: Optional[int] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """認証試行のログを、許可イベントへ正規化して記録する"""
        extra = additional_data or {}
        auth_method = self._extract_auth_method(extra)
        event_type = self._authentication_event_type(
            success=success,
            failure_reason=failure_reason,
            auth_method=auth_method,
        )
        severity = "info" if success else "warning"

        event_data = self._build_base_event_data(
            event_type,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
            auth_method=auth_method,
            failure_reason=failure_reason,
            request_id=extra.get("request_id"),
            username=extra.get("username"),
            endpoint=extra.get("endpoint"),
            subject_id=extra.get("subject_id"),
            sso_provider=extra.get("sso_provider"),
            saml_provider=extra.get("saml_provider"),
        )

        self._pick_log_method(severity)("Security event", **event_data)

    def log_account_lockout(
        self,
        email: str,
        ip_address: str,
        lockout_type: str,
        attempt_count: int,
        lockout_duration: int,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """アカウントロックアウトを限定イベントで記録する"""
        extra = additional_data or {}
        failure_reason = extra.get("failure_reason") or extra.get("reason") or lockout_type
        event_data = self._build_base_event_data(
            SECURITY_EVENT_AUTHENTICATION_BLOCKED_LOCKOUT,
            email=email,
            ip_address=ip_address,
            auth_method=self._extract_auth_method(extra),
            failure_reason=failure_reason,
            lockout_duration=lockout_duration,
            count=attempt_count,
            request_id=extra.get("request_id"),
            username=extra.get("username"),
            endpoint=extra.get("endpoint"),
        )

        self.security_logger.warning("Security event", **event_data)

    def log_suspicious_activity(
        self,
        activity_type: str,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
        severity: str = "warning",
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """疑わしい活動を限定イベントで記録する"""
        extra = additional_data or {}
        failure_reason = description or activity_type
        event_data = self._build_base_event_data(
            SECURITY_EVENT_SUSPICIOUS_ACTIVITY_DETECTED,
            email=email,
            ip_address=ip_address,
            user_id=user_id,
            failure_reason=failure_reason,
            request_id=extra.get("request_id"),
            endpoint=extra.get("endpoint"),
            subject_id=extra.get("subject_id"),
            username=extra.get("username"),
        )

        self._pick_log_method(severity)("Security event", **event_data)

    def log_security_event(
        self,
        event_type: str,
        severity: str = "info",
        **kwargs: Any,
    ) -> None:
        """許可済みイベントだけを security logger へ送る"""
        event_data = self._build_base_event_data(event_type, **kwargs)
        self._pick_log_method(severity)("Security event", **event_data)

    def log_rate_limit_exceeded(
        self,
        endpoint: str,
        ip_address: str,
        user_id: Optional[int] = None,
        limit_type: str = "general",
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """security-sensitive endpoint のレート制限超過を記録する"""
        extra = additional_data or {}
        event_data = self._build_base_event_data(
            SECURITY_EVENT_RATE_LIMIT_EXCEEDED_SECURITY_SENSITIVE_ENDPOINT,
            endpoint=endpoint,
            ip_address=ip_address,
            user_id=user_id,
            failure_reason=limit_type,
            request_id=extra.get("request_id"),
            username=extra.get("username"),
            auth_method=self._extract_auth_method(extra),
        )

        self.security_logger.warning("Security event", **event_data)


# グローバルインスタンス
security_logger = SecurityLogger()
