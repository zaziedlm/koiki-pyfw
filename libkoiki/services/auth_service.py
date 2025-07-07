# src/services/auth_service.py
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
import structlog

from libkoiki.repositories.refresh_token_repository import RefreshTokenRepository
from libkoiki.repositories.user_repository import UserRepository
from libkoiki.models.refresh_token import RefreshTokenModel
from libkoiki.models.user import UserModel
from libkoiki.core.security import (
    create_token_pair,
    verify_refresh_token_format,
    extract_device_info,
    hash_refresh_token
)
from libkoiki.core.exceptions import AuthenticationException, ValidationException
from libkoiki.core.transaction import transactional
from libkoiki.core.config import settings

logger = structlog.get_logger(__name__)

class AuthService:
    """認証サービス（リフレッシュトークン機能拡張）"""
    
    def __init__(self, refresh_token_repo: RefreshTokenRepository, user_repo: UserRepository):
        self.refresh_token_repo = refresh_token_repo
        self.user_repo = user_repo
    
    @transactional
    async def create_token_pair(
        self, 
        user: UserModel, 
        db: AsyncSession,
        device_info: Optional[str] = None
    ) -> Tuple[str, str, int]:
        """
        ユーザーのアクセストークンとリフレッシュトークンのペアを作成します。
        
        Args:
            user: ユーザーモデル
            db: データベースセッション
            device_info: デバイス情報（JSON文字列）
            
        Returns:
            タプル: (access_token, refresh_token, expires_in_seconds)
        """
        logger.info("Creating token pair", user_id=user.id)
        
        # セッションをリポジトリに設定
        self.refresh_token_repo.set_session(db)
        
        # トークンペア生成
        access_token, refresh_token, expires_in = create_token_pair(user.id, device_info)
        
        # リフレッシュトークンをデータベースに保存
        expires_at = RefreshTokenModel.create_expires_at(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.refresh_token_repo.create_refresh_token(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
            device_info=device_info
        )
        
        logger.info("Token pair created successfully", user_id=user.id)
        return access_token, refresh_token, expires_in
    
    @transactional
    async def refresh_access_token(
        self, 
        refresh_token: str, 
        db: AsyncSession,
        device_info: Optional[str] = None,
        enable_rotation: bool = True
    ) -> Tuple[str, Optional[str], int]:
        """
        リフレッシュトークンを使ってアクセストークンを更新します。
        
        Args:
            refresh_token: リフレッシュトークン
            db: データベースセッション
            device_info: デバイス情報
            enable_rotation: トークンローテーションを有効にするか
            
        Returns:
            タプル: (access_token, new_refresh_token, expires_in_seconds)
            
        Raises:
            AuthenticationException: トークンが無効な場合
        """
        logger.debug("Refreshing access token", token_prefix=refresh_token[:10] + "...")
        
        # トークン形式検証
        if not verify_refresh_token_format(refresh_token):
            logger.warning("Invalid refresh token format")
            raise AuthenticationException("Invalid refresh token format")
        
        # セッションをリポジトリに設定
        self.refresh_token_repo.set_session(db)
        self.user_repo.set_session(db)
        
        # リフレッシュトークンを検証
        refresh_token_model = await self.refresh_token_repo.get_valid_token(refresh_token)
        
        if not refresh_token_model:
            logger.warning("Refresh token not found or invalid")
            raise AuthenticationException("Invalid or expired refresh token")
        
        # ユーザーを取得
        user = await self.user_repo.get(refresh_token_model.user_id)
        if not user or not user.is_active:
            logger.warning("User not found or inactive", user_id=refresh_token_model.user_id)
            raise AuthenticationException("User not found or inactive")
        
        # 最終使用時刻を更新
        await self.refresh_token_repo.update_last_used(refresh_token)
        
        # 新しいアクセストークンを生成
        from libkoiki.core.security import create_access_token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires
        )
        
        new_refresh_token = None
        
        # トークンローテーション（オプション）
        if enable_rotation:
            logger.debug("Token rotation enabled", user_id=user.id)
            
            # 古いトークンを無効化
            await self.refresh_token_repo.revoke_token(refresh_token)
            
            # 新しいリフレッシュトークンを生成
            from libkoiki.core.security import generate_refresh_token
            new_refresh_token = generate_refresh_token()
            
            # 新しいリフレッシュトークンを保存
            expires_at = RefreshTokenModel.create_expires_at(days=7)
            await self.refresh_token_repo.create_refresh_token(
                user_id=user.id,
                token=new_refresh_token,
                expires_at=expires_at,
                device_info=device_info
            )
        
        logger.info(
            "Access token refreshed successfully", 
            user_id=user.id, 
            rotation_enabled=enable_rotation
        )
        
        return new_access_token, new_refresh_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    @transactional
    async def revoke_user_tokens(
        self, 
        user_id: int, 
        db: AsyncSession,
        exclude_current: bool = False,
        current_token: Optional[str] = None
    ) -> int:
        """
        ユーザーのすべてのリフレッシュトークンを無効化します。
        
        Args:
            user_id: ユーザーID
            db: データベースセッション
            exclude_current: 現在のトークンを除外するか
            current_token: 現在のトークン（除外する場合）
            
        Returns:
            無効化されたトークンの数
        """
        logger.info("Revoking user tokens", user_id=user_id, exclude_current=exclude_current)
        
        self.refresh_token_repo.set_session(db)
        
        exclude_token_id = None
        if exclude_current and current_token:
            current_token_model = await self.refresh_token_repo.get_by_token(current_token)
            if current_token_model:
                exclude_token_id = current_token_model.id
        
        revoked_count = await self.refresh_token_repo.revoke_user_tokens(
            user_id=user_id,
            exclude_token_id=exclude_token_id
        )
        
        logger.info("User tokens revoked", user_id=user_id, count=revoked_count)
        return revoked_count
    
    async def get_user_tokens(
        self, 
        user_id: int, 
        db: AsyncSession,
        only_valid: bool = True
    ) -> list[RefreshTokenModel]:
        """
        ユーザーのリフレッシュトークン一覧を取得します。
        
        Args:
            user_id: ユーザーID
            db: データベースセッション
            only_valid: 有効なトークンのみを取得するか
            
        Returns:
            リフレッシュトークンのリスト
        """
        self.refresh_token_repo.set_session(db)
        return await self.refresh_token_repo.get_user_tokens(user_id, only_valid)
    
    @transactional
    async def cleanup_expired_tokens(self, db: AsyncSession) -> int:
        """
        期限切れのリフレッシュトークンをクリーンアップします。
        
        Args:
            db: データベースセッション
            
        Returns:
            削除されたトークンの数
        """
        self.refresh_token_repo.set_session(db)
        return await self.refresh_token_repo.cleanup_expired_tokens()