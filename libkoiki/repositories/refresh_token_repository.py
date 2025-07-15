# src/repositories/refresh_token_repository.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from libkoiki.models.refresh_token import RefreshTokenModel
from libkoiki.core.security import hash_refresh_token
import structlog

logger = structlog.get_logger(__name__)

class RefreshTokenRepository:
    """リフレッシュトークンリポジトリ"""
    
    def __init__(self):
        self.session: Optional[AsyncSession] = None
    
    def set_session(self, session: AsyncSession) -> None:
        """データベースセッションを設定"""
        self.session = session
    
    async def create_refresh_token(
        self, 
        user_id: int, 
        token: str, 
        expires_at: datetime,
        device_info: Optional[str] = None
    ) -> RefreshTokenModel:
        """
        新しいリフレッシュトークンを作成します。
        
        Args:
            user_id: ユーザーID
            token: 平文のリフレッシュトークン
            expires_at: 有効期限
            device_info: デバイス情報（JSON文字列）
            
        Returns:
            作成されたリフレッシュトークンモデル
        """
        token_hash = hash_refresh_token(token)
        
        refresh_token = RefreshTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_info=device_info
        )
        
        self.session.add(refresh_token)
        await self.session.commit()
        await self.session.refresh(refresh_token)
        return refresh_token
    
    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshTokenModel]:
        """
        トークンハッシュでリフレッシュトークンを取得します。
        
        Args:
            token_hash: ハッシュ化されたトークン
            
        Returns:
            見つかったリフレッシュトークン、または None
        """
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == token_hash
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_token(self, token: str) -> Optional[RefreshTokenModel]:
        """
        平文トークンでリフレッシュトークンを取得します。
        
        Args:
            token: 平文のリフレッシュトークン
            
        Returns:
            見つかったリフレッシュトークン、または None
        """
        token_hash = hash_refresh_token(token)
        return await self.get_by_token_hash(token_hash)
    
    async def get_valid_token(self, token: str) -> Optional[RefreshTokenModel]:
        """
        有効なリフレッシュトークンを取得します。
        
        Args:
            token: 平文のリフレッシュトークン
            
        Returns:
            有効なリフレッシュトークン、または None
        """
        refresh_token = await self.get_by_token(token)
        
        if not refresh_token:
            logger.debug("Refresh token not found")
            return None
            
        if refresh_token.is_revoked:
            logger.debug("Refresh token is revoked", token_id=refresh_token.id)
            return None
            
        if refresh_token.is_expired:
            logger.debug("Refresh token is expired", token_id=refresh_token.id)
            return None
        
        return refresh_token
    
    async def get_user_tokens(self, user_id: int, only_valid: bool = True) -> List[RefreshTokenModel]:
        """
        ユーザーのリフレッシュトークン一覧を取得します。
        
        Args:
            user_id: ユーザーID
            only_valid: 有効なトークンのみを取得するか
            
        Returns:
            リフレッシュトークンのリスト
        """
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id
        )
        
        if only_valid:
            stmt = stmt.where(
                and_(
                    RefreshTokenModel.is_revoked == False,
                    RefreshTokenModel.expires_at > datetime.now(timezone.utc)
                )
            )
        
        stmt = stmt.order_by(RefreshTokenModel.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def revoke_token(self, token: str) -> bool:
        """
        リフレッシュトークンを無効化します。
        
        Args:
            token: 平文のリフレッシュトークン
            
        Returns:
            無効化が成功したかどうか
        """
        refresh_token = await self.get_by_token(token)
        
        if not refresh_token:
            logger.debug("Token not found for revocation")
            return False
        
        refresh_token.revoke()
        await self.session.commit()
        
        logger.info("Refresh token revoked", token_id=refresh_token.id, user_id=refresh_token.user_id)
        return True
    
    async def revoke_user_tokens(self, user_id: int, exclude_token_id: Optional[int] = None) -> int:
        """
        ユーザーのすべてのリフレッシュトークンを無効化します。
        
        Args:
            user_id: ユーザーID
            exclude_token_id: 除外するトークンID（現在のトークンを除外する場合）
            
        Returns:
            無効化されたトークンの数
        """
        stmt = select(RefreshTokenModel).where(
            and_(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.is_revoked == False
            )
        )
        
        if exclude_token_id:
            stmt = stmt.where(RefreshTokenModel.id != exclude_token_id)
        
        result = await self.session.execute(stmt)
        tokens = list(result.scalars().all())
        
        count = 0
        for token in tokens:
            token.revoke()
            count += 1
        
        if count > 0:
            await self.session.commit()
            logger.info("Revoked user tokens", user_id=user_id, count=count)
        
        return count
    
    async def update_last_used(self, token: str) -> bool:
        """
        リフレッシュトークンの最終使用時刻を更新します。
        
        Args:
            token: 平文のリフレッシュトークン
            
        Returns:
            更新が成功したかどうか
        """
        refresh_token = await self.get_by_token(token)
        
        if not refresh_token:
            return False
        
        refresh_token.update_last_used()
        await self.session.commit()
        
        return True
    
    async def cleanup_expired_tokens(self) -> int:
        """
        期限切れのリフレッシュトークンを削除します。
        
        Returns:
            削除されたトークンの数
        """
        stmt = delete(RefreshTokenModel).where(
            RefreshTokenModel.expires_at < datetime.now(timezone.utc)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info("Cleaned up expired refresh tokens", count=deleted_count)
        
        return deleted_count