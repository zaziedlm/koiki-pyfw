# src/models/password_reset.py
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from libkoiki.db.base import Base


class PasswordResetModel(Base):
    """パスワードリセットトークンモデル"""

    __tablename__ = "password_reset_tokens"

    # BaseからのIDカラムを使用（手動定義不要）
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    # Baseからのcreated_atを使用（重複定義を削除）
    used_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6対応
    user_agent = Column(Text, nullable=True)

    # リレーションシップ
    user = relationship("UserModel", back_populates="password_reset_tokens")

    @classmethod
    def create_token_expiry(cls, hours: int = 1) -> datetime:
        """トークンの有効期限を設定（デフォルト1時間）"""
        return datetime.now(timezone.utc) + timedelta(hours=hours)

    def is_expired(self) -> bool:
        """トークンが期限切れかどうかを確認"""
        now = datetime.now(timezone.utc)
        return now > self.expires_at

    def is_valid(self) -> bool:
        """トークンが有効かどうかを確認"""
        return not self.is_used and not self.is_expired()
