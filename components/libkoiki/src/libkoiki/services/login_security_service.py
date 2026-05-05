# src/services/login_security_service.py
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from libkoiki.core.config import settings
from libkoiki.core.exceptions import AuthenticationException
from libkoiki.core.security_config import get_login_security_config
from libkoiki.models.login_attempt import LoginAttemptModel
from libkoiki.repositories.login_attempt_repository import LoginAttemptRepository


class LoginSecurityService:
    """ログインセキュリティサービス（試行制限、アカウントロックアウト等）"""

    def __init__(self, login_attempt_repository: LoginAttemptRepository):
        self.login_attempt_repository = login_attempt_repository
        
        # 設定値を外部設定から取得
        self.config = get_login_security_config()
        
    @property
    def max_attempts_per_email(self) -> int:
        return self.config.max_attempts_per_email
    
    @property
    def max_attempts_per_ip(self) -> int:
        return self.config.max_attempts_per_ip
    
    @property
    def lockout_duration_minutes(self) -> int:
        return self.config.lockout_duration_minutes
    
    @property
    def progressive_delay_base(self) -> int:
        return self.config.progressive_delay_base

    async def check_login_allowed(
        self, email: str, ip_address: str, db: AsyncSession
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        ログイン試行が許可されているかチェック

        Returns:
            (is_allowed, reason, retry_after_seconds)
        """
        # セッションを設定
        self.login_attempt_repository.set_session(db)

        # メールアドレス単位のチェック
        email_attempts = (
            await self.login_attempt_repository.count_recent_failed_attempts_by_email(
                email, self.lockout_duration_minutes
            )
        )

        if email_attempts >= self.max_attempts_per_email:
            return (
                False,
                f"Account temporarily locked due to {email_attempts} failed attempts",
                self.lockout_duration_minutes * 60,
            )

        # IP単位のチェック
        ip_attempts = (
            await self.login_attempt_repository.count_recent_failed_attempts_by_ip(
                ip_address, self.lockout_duration_minutes
            )
        )

        if ip_attempts >= self.max_attempts_per_ip:
            return (
                False,
                f"IP temporarily blocked due to {ip_attempts} failed attempts",
                self.lockout_duration_minutes * 60,
            )

        return True, None, None

    async def record_login_attempt(
        self,
        email: str,
        ip_address: str,
        is_successful: bool,
        db: AsyncSession,
        user_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> LoginAttemptModel:
        """ログイン試行を記録"""
        # セッションを設定
        self.login_attempt_repository.set_session(db)

        return await self.login_attempt_repository.record_attempt(
            email=email,
            ip_address=ip_address,
            is_successful=is_successful,
            user_id=user_id,
            user_agent=user_agent,
            failure_reason=failure_reason,
        )

    async def get_progressive_delay(
        self, email: str, ip_address: str, db: AsyncSession
    ) -> int:
        """
        段階的遅延時間を計算

        Returns:
            delay_seconds
        """
        # セッションを設定
        self.login_attempt_repository.set_session(db)

        # 最近の失敗試行数を取得
        email_attempts = (
            await self.login_attempt_repository.count_recent_failed_attempts_by_email(
                email, self.lockout_duration_minutes
            )
        )
        ip_attempts = (
            await self.login_attempt_repository.count_recent_failed_attempts_by_ip(
                ip_address, self.lockout_duration_minutes
            )
        )

        # より多い試行数を使用
        max_attempts = max(email_attempts, ip_attempts)

        if max_attempts <= 1:
            return 0

        # 指数関数的な遅延（上限あり）
        delay = min(self.progressive_delay_base ** (max_attempts - 1), self.config.max_progressive_delay)
        return int(delay)

    async def apply_progressive_delay(
        self, email: str, ip_address: str, db: AsyncSession
    ) -> None:
        """段階的遅延を適用"""
        delay = await self.get_progressive_delay(email, ip_address, db)
        if delay > 0:
            await asyncio.sleep(delay)

    async def get_lockout_status(
        self, email: str, ip_address: str, db: AsyncSession
    ) -> dict:
        """ロックアウト状況を取得"""
        # セッションを設定
        self.login_attempt_repository.set_session(db)

        email_attempts = (
            await self.login_attempt_repository.count_recent_failed_attempts_by_email(
                email, self.lockout_duration_minutes
            )
        )
        ip_attempts = (
            await self.login_attempt_repository.count_recent_failed_attempts_by_ip(
                ip_address, self.lockout_duration_minutes
            )
        )

        email_locked = email_attempts >= self.max_attempts_per_email
        ip_locked = ip_attempts >= self.max_attempts_per_ip

        return {
            "email_attempts": email_attempts,
            "email_max_attempts": self.max_attempts_per_email,
            "email_locked": email_locked,
            "ip_attempts": ip_attempts,
            "ip_max_attempts": self.max_attempts_per_ip,
            "ip_locked": ip_locked,
            "lockout_duration_minutes": self.lockout_duration_minutes,
            "is_locked": email_locked or ip_locked,
        }

    async def get_last_successful_login(
        self, email: str, db: AsyncSession
    ) -> Optional[LoginAttemptModel]:
        """最後の成功ログインを取得"""
        # セッションを設定
        self.login_attempt_repository.set_session(db)

        return await self.login_attempt_repository.get_last_successful_attempt(email)

    async def cleanup_old_attempts(self, db: AsyncSession, days: int = 30) -> int:
        """古いログイン試行履歴をクリーンアップ"""
        # セッションを設定
        self.login_attempt_repository.set_session(db)

        return await self.login_attempt_repository.cleanup_old_attempts(days)
