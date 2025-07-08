# src/repositories/login_attempt_repository.py
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_, desc, func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from libkoiki.models.login_attempt import LoginAttemptModel


class LoginAttemptRepository:
    """ログイン試行履歴のリポジトリ"""

    def __init__(self):
        self.session: Optional[AsyncSession] = None

    def set_session(self, session: AsyncSession) -> None:
        """データベースセッションを設定"""
        self.session = session

    async def record_attempt(
        self,
        email: str,
        ip_address: str,
        is_successful: bool,
        user_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> LoginAttemptModel:
        """ログイン試行を記録"""
        if not self.session:
            raise RuntimeError("Database session not initialized")

        attempt = LoginAttemptModel(
            email=email,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            is_successful=is_successful,
            failure_reason=failure_reason,
        )

        self.session.add(attempt)
        await self.session.flush()  # フラッシュしてIDを取得
        await self.session.refresh(attempt)  # 最新データで更新（created_at等）

        return attempt

    async def get_recent_failed_attempts_by_email(
        self, email: str, minutes: int = 15
    ) -> List[LoginAttemptModel]:
        """指定時間内のメールアドレス別失敗試行を取得"""
        if not self.session:
            raise RuntimeError("Database session not initialized")

        window_start = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        query = (
            select(LoginAttemptModel)
            .where(
                and_(
                    LoginAttemptModel.email == email,
                    LoginAttemptModel.is_successful == False,
                    LoginAttemptModel.attempted_at >= window_start,
                )
            )
            .order_by(desc(LoginAttemptModel.attempted_at))
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_recent_failed_attempts_by_ip(
        self, ip_address: str, minutes: int = 15
    ) -> List[LoginAttemptModel]:
        """指定時間内のIP別失敗試行を取得"""
        if not self.session:
            raise RuntimeError("Database session not initialized")

        window_start = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        query = (
            select(LoginAttemptModel)
            .where(
                and_(
                    LoginAttemptModel.ip_address == ip_address,
                    LoginAttemptModel.is_successful == False,
                    LoginAttemptModel.attempted_at >= window_start,
                )
            )
            .order_by(desc(LoginAttemptModel.attempted_at))
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_recent_failed_attempts_by_email(
        self, email: str, minutes: int = 15
    ) -> int:
        """指定時間内のメールアドレス別失敗試行数を取得"""
        if not self.session:
            raise RuntimeError("Database session not initialized")

        window_start = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        query = select(func.count(LoginAttemptModel.id)).where(
            and_(
                LoginAttemptModel.email == email,
                LoginAttemptModel.is_successful == False,
                LoginAttemptModel.attempted_at >= window_start,
            )
        )

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_recent_failed_attempts_by_ip(
        self, ip_address: str, minutes: int = 15
    ) -> int:
        """指定時間内のIP別失敗試行数を取得"""
        if not self.session:
            raise RuntimeError("Database session not initialized")

        window_start = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        query = select(func.count(LoginAttemptModel.id)).where(
            and_(
                LoginAttemptModel.ip_address == ip_address,
                LoginAttemptModel.is_successful == False,
                LoginAttemptModel.attempted_at >= window_start,
            )
        )

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_last_successful_attempt(
        self, email: str
    ) -> Optional[LoginAttemptModel]:
        """最後の成功ログイン試行を取得"""
        if not self.session:
            raise RuntimeError("Database session not initialized")

        query = (
            select(LoginAttemptModel)
            .where(
                and_(
                    LoginAttemptModel.email == email,
                    LoginAttemptModel.is_successful == True,
                )
            )
            .order_by(desc(LoginAttemptModel.attempted_at))
        )

        result = await self.session.execute(query)
        return result.scalars().first()

    async def cleanup_old_attempts(self, days: int = 30) -> int:
        """古いログイン試行履歴を削除（バッチ削除で最適化）"""
        if not self.session:
            raise RuntimeError("Database session not initialized")

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # 効率的なバッチ削除を実行
        delete_query = delete(LoginAttemptModel).where(
            LoginAttemptModel.attempted_at < cutoff_date
        )

        result = await self.session.execute(delete_query)
        deleted_count = result.rowcount

        return deleted_count
