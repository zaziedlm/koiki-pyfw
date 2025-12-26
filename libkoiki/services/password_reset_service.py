# src/services/password_reset_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import secrets
import string

from libkoiki.repositories.password_reset_repository import PasswordResetRepository
from libkoiki.models.password_reset import PasswordResetModel
from libkoiki.models.user import UserModel
from libkoiki.core.exceptions import ValidationException


class PasswordResetService:
    """パスワードリセットサービス"""

    def __init__(self, password_reset_repository: PasswordResetRepository):
        self.password_reset_repository = password_reset_repository

    def generate_reset_token(self, length: int = 32) -> str:
        """安全なリセットトークンを生成"""
        # URL-safe な文字列を使用
        alphabet = string.ascii_letters + string.digits + '-_'
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    async def create_reset_token(
        self, 
        user: UserModel,
        db: AsyncSession,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_hours: int = 1
    ) -> Tuple[str, PasswordResetModel]:
        """パスワードリセットトークンを作成"""
        # セッションを設定
        self.password_reset_repository.session = db
        
        # 既存の有効なトークンを無効化
        await self.password_reset_repository.revoke_user_tokens(user.id)
        
        # 新しいトークンを生成
        token = self.generate_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
        
        # トークンをデータベースに保存
        reset_token = await self.password_reset_repository.create_reset_token(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return token, reset_token

    async def validate_reset_token(
        self, 
        token: str, 
        db: AsyncSession
    ) -> PasswordResetModel:
        """リセットトークンの検証"""
        # セッションを設定
        self.password_reset_repository.session = db
        
        # トークンを取得
        reset_token = await self.password_reset_repository.get_valid_token(token)
        
        if not reset_token:
            raise ValidationException("Invalid or expired password reset token")
        
        if not reset_token.is_valid():
            raise ValidationException("Password reset token has expired or been used")
        
        return reset_token

    async def complete_password_reset(
        self, 
        token: str, 
        new_password: str,
        db: AsyncSession
    ) -> UserModel:
        """パスワードリセットを完了"""
        # トークンを検証
        reset_token = await self.validate_reset_token(token, db)
        
        # トークンを使用済みにマーク
        await self.password_reset_repository.mark_token_as_used(reset_token.id)
        
        # ユーザーを返す（パスワード更新は呼び出し元で行う）
        return reset_token.user

    async def cleanup_expired_tokens(self, db: AsyncSession) -> int:
        """期限切れトークンをクリーンアップ"""
        # セッションを設定
        self.password_reset_repository.session = db
        
        return await self.password_reset_repository.cleanup_expired_tokens()

    async def get_user_active_tokens_count(self, user_id: int, db: AsyncSession) -> int:
        """ユーザーの有効なリセットトークン数を取得"""
        # セッションを設定
        self.password_reset_repository.session = db
        
        active_tokens = await self.password_reset_repository.get_user_active_tokens(user_id)
        return len(active_tokens)

    async def revoke_user_tokens(self, user_id: int, db: AsyncSession) -> int:
        """ユーザーの全リセットトークンを無効化"""
        # セッションを設定
        self.password_reset_repository.session = db
        
        return await self.password_reset_repository.revoke_user_tokens(user_id)
