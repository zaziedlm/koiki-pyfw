# src/repositories/password_reset_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from datetime import datetime, timedelta
from typing import Optional, List
import hashlib

from libkoiki.models.password_reset import PasswordResetModel


class PasswordResetRepository:
    """パスワードリセットトークンのリポジトリ"""

    def __init__(self):
        self.session: Optional[AsyncSession] = None

    async def create_reset_token(
        self, 
        user_id: int, 
        token: str, 
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PasswordResetModel:
        """パスワードリセットトークンを作成"""
        if not self.session:
            raise RuntimeError("Database session not initialized")
        
        # トークンをハッシュ化
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        reset_token = PasswordResetModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.session.add(reset_token)
        await self.session.commit()
        await self.session.refresh(reset_token)
        
        return reset_token

    async def get_valid_token(self, token: str) -> Optional[PasswordResetModel]:
        """有効なリセットトークンを取得"""
        if not self.session:
            raise RuntimeError("Database session not initialized")
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        query = select(PasswordResetModel).where(
            and_(
                PasswordResetModel.token_hash == token_hash,
                PasswordResetModel.is_used == False,
                PasswordResetModel.expires_at > datetime.utcnow()
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().first()

    async def mark_token_as_used(self, token_id: int) -> None:
        """トークンを使用済みにマーク"""
        if not self.session:
            raise RuntimeError("Database session not initialized")
        
        query = select(PasswordResetModel).where(PasswordResetModel.id == token_id)
        result = await self.session.execute(query)
        token = result.scalars().first()
        
        if token:
            token.is_used = True
            token.used_at = datetime.utcnow()
            await self.session.commit()

    async def cleanup_expired_tokens(self, user_id: Optional[int] = None) -> int:
        """期限切れトークンの削除"""
        if not self.session:
            raise RuntimeError("Database session not initialized")
        
        query = select(PasswordResetModel).where(
            PasswordResetModel.expires_at < datetime.utcnow()
        )
        
        if user_id:
            query = query.where(PasswordResetModel.user_id == user_id)
        
        result = await self.session.execute(query)
        expired_tokens = result.scalars().all()
        
        for token in expired_tokens:
            await self.session.delete(token)
        
        await self.session.commit()
        return len(expired_tokens)

    async def get_user_active_tokens(self, user_id: int) -> List[PasswordResetModel]:
        """ユーザーの有効なリセットトークンを取得"""
        if not self.session:
            raise RuntimeError("Database session not initialized")
        
        query = select(PasswordResetModel).where(
            and_(
                PasswordResetModel.user_id == user_id,
                PasswordResetModel.is_used == False,
                PasswordResetModel.expires_at > datetime.utcnow()
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def revoke_user_tokens(self, user_id: int) -> int:
        """ユーザーの全リセットトークンを無効化"""
        if not self.session:
            raise RuntimeError("Database session not initialized")
        
        query = select(PasswordResetModel).where(
            and_(
                PasswordResetModel.user_id == user_id,
                PasswordResetModel.is_used == False
            )
        )
        
        result = await self.session.execute(query)
        active_tokens = result.scalars().all()
        
        for token in active_tokens:
            token.is_used = True
            token.used_at = datetime.utcnow()
        
        await self.session.commit()
        return len(active_tokens)