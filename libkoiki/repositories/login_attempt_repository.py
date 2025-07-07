# src/repositories/login_attempt_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func, desc
from datetime import datetime, timedelta
from typing import Optional, List

from libkoiki.models.login_attempt import LoginAttemptModel


class LoginAttemptRepository:
    """ログイン試行履歴のリポジトリ"""

    def __init__(self):
        self.session: Optional[AsyncSession] = None

    async def record_attempt(
        self,
        email: str,
        ip_address: str,
        is_successful: bool,
        user_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
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
            failure_reason=failure_reason
        )
        
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)
        
        return attempt

    async def get_recent_failed_attempts_by_email(
        self, 
        email: str, 
        minutes: int = 15
    ) -> List[LoginAttemptModel]:
        """指定時間内のメールアドレス別失敗試行を取得"""
        if not self.session:
            raise RuntimeError("Database session not initialized")
        
        window_start = datetime.utcnow() - timedelta(minutes=minutes)
        
        query = select(LoginAttemptModel).where(
            and_(
                LoginAttemptModel.email == email,
                LoginAttemptModel.is_successful == False,
                LoginAttemptModel.attempted_at >= window_start
            )
        ).order_by(desc(LoginAttemptModel.attempted_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_recent_failed_attempts_by_ip(
        self, 
        ip_address: str, 
        minutes: int = 15
    ) -> List[LoginAttemptModel]:
        """指定時間内のIP別失敗試行を取得"""
        if not self.session:
            raise RuntimeError("Database session not initialized")
        
        window_start = datetime.utcnow() - timedelta(minutes=minutes)
        
        query = select(LoginAttemptModel).where(
            and_(
                LoginAttemptModel.ip_address == ip_address,
                LoginAttemptModel.is_successful == False,
                LoginAttemptModel.attempted_at >= window_start
            )
        ).order_by(desc(LoginAttemptModel.attempted_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_recent_failed_attempts_by_email(
        self, 
        email: str, 
        minutes: int = 15
    ) -> int:
        """指定時間内のメールアドレス別失敗試行数を取得"""
        if not self.session:
            raise RuntimeError("Database session not initialized")
        
        window_start = datetime.utcnow() - timedelta(minutes=minutes)
        
        query = select(func.count(LoginAttemptModel.id)).where(
            and_(
                LoginAttemptModel.email == email,
                LoginAttemptModel.is_successful == False,
                LoginAttemptModel.attempted_at >= window_start
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_recent_failed_attempts_by_ip(
        self, 
        ip_address: str, 
        minutes: int = 15
    ) -> int:
        """指定時間内のIP別失敗試行数を取得"""
        if not self.session:
            raise RuntimeError("Database session not initialized")
        
        window_start = datetime.utcnow() - timedelta(minutes=minutes)
        
        query = select(func.count(LoginAttemptModel.id)).where(
            and_(
                LoginAttemptModel.ip_address == ip_address,
                LoginAttemptModel.is_successful == False,
                LoginAttemptModel.attempted_at >= window_start
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_last_successful_attempt(self, email: str) -> Optional[LoginAttemptModel]:
        """最後の成功ログイン試行を取得"""
        if not self.session:
            raise RuntimeError("Database session not initialized")
        
        query = select(LoginAttemptModel).where(
            and_(
                LoginAttemptModel.email == email,
                LoginAttemptModel.is_successful == True
            )
        ).order_by(desc(LoginAttemptModel.attempted_at))
        
        result = await self.session.execute(query)
        return result.scalars().first()

    async def cleanup_old_attempts(self, days: int = 30) -> int:
        """古いログイン試行履歴を削除"""
        if not self.session:
            raise RuntimeError("Database session not initialized")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(LoginAttemptModel).where(
            LoginAttemptModel.attempted_at < cutoff_date
        )
        
        result = await self.session.execute(query)
        old_attempts = result.scalars().all()
        
        for attempt in old_attempts:
            await self.session.delete(attempt)
        
        await self.session.commit()
        return len(old_attempts)