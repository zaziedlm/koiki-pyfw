# src/core/security_logger.py
"""
セキュリティイベント専用のロガー
セキュリティ関連のイベントを構造化してログ出力
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger(__name__)


class SecurityLogger:
    """セキュリティイベント専用ロガー"""

    def __init__(self):
        self.security_logger = structlog.get_logger("security")

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
        """認証試行のログを記録"""
        event_data = {
            "event_type": "authentication_attempt",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "email": email,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "failure_reason": failure_reason,
            "user_id": user_id,
        }
        
        if additional_data:
            event_data.update(additional_data)

        self.security_logger.info(
            "Authentication attempt",
            **event_data
        )

    def log_account_lockout(
        self,
        email: str,
        ip_address: str,
        lockout_type: str,  # "email" or "ip"
        attempt_count: int,
        lockout_duration: int,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """アカウントロックアウトのログを記録"""
        event_data = {
            "event_type": "account_lockout",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "email": email,
            "ip_address": ip_address,
            "lockout_type": lockout_type,
            "attempt_count": attempt_count,
            "lockout_duration_seconds": lockout_duration,
        }
        
        if additional_data:
            event_data.update(additional_data)

        self.security_logger.warning(
            "Account lockout triggered",
            **event_data
        )

    def log_suspicious_activity(
        self,
        activity_type: str,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
        severity: str = "medium",
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """疑わしい活動のログを記録"""
        event_data = {
            "event_type": "suspicious_activity",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "activity_type": activity_type,
            "email": email,
            "ip_address": ip_address,
            "user_id": user_id,
            "description": description,
            "severity": severity,
        }
        
        if additional_data:
            event_data.update(additional_data)

        log_method = getattr(self.security_logger, severity, self.security_logger.warning)
        log_method(
            "Suspicious activity detected",
            **event_data
        )

    def log_security_event(
        self,
        event_type: str,
        severity: str = "info",
        **kwargs: Any,
    ) -> None:
        """汎用的なセキュリティイベントのログを記録"""
        event_data = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }

        log_method = getattr(self.security_logger, severity, self.security_logger.info)
        log_method(
            f"Security event: {event_type}",
            **event_data
        )

    def log_rate_limit_exceeded(
        self,
        endpoint: str,
        ip_address: str,
        user_id: Optional[int] = None,
        limit_type: str = "general",
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """レート制限超過のログを記録"""
        event_data = {
            "event_type": "rate_limit_exceeded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": endpoint,
            "ip_address": ip_address,
            "user_id": user_id,
            "limit_type": limit_type,
        }
        
        if additional_data:
            event_data.update(additional_data)

        self.security_logger.warning(
            "Rate limit exceeded",
            **event_data
        )


# グローバルインスタンス
security_logger = SecurityLogger()