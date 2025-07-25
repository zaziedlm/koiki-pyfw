# src/models/refresh_token.py
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from libkoiki.db.base import Base


class RefreshTokenModel(Base):
    """リフレッシュトークンモデル"""

    __tablename__ = "refresh_tokens"

    # BaseからのIDカラムを使用（手動定義不要）
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    device_info = Column(Text, nullable=True)  # JSON文字列として保存
    # Baseからのcreated_atを使用（重複定義を削除）
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Base class の updated_at は不要だが要件を満たすため None に設定
    updated_at = None

    # リレーション
    user = relationship("UserModel", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at}, is_revoked={self.is_revoked})>"

    @property
    def is_expired(self) -> bool:
        """トークンが期限切れかどうかを判定"""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """トークンが有効かどうかを判定"""
        return not self.is_revoked and not self.is_expired

    def revoke(self):
        """トークンを無効化"""
        self.is_revoked = True

    def update_last_used(self):
        """最終使用時刻を更新"""
        self.last_used_at = datetime.now(timezone.utc)

    @classmethod
    def create_expires_at(cls, days: int = 7) -> datetime:
        """有効期限を生成（デフォルト7日）"""
        return datetime.now(timezone.utc) + timedelta(days=days)
