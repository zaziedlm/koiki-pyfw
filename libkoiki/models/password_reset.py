# src/models/password_reset.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from typing import Optional

from libkoiki.db.base import Base


class PasswordResetModel(Base):
    """パスワードリセットトークンモデル"""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6対応
    user_agent = Column(Text, nullable=True)

    # リレーションシップ
    user = relationship("UserModel", back_populates="password_reset_tokens")

    @classmethod
    def create_token_expiry(cls, hours: int = 1) -> datetime:
        """トークンの有効期限を設定（デフォルト1時間）"""
        return datetime.utcnow() + timedelta(hours=hours)

    def is_expired(self) -> bool:
        """トークンが期限切れかどうかを確認"""
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """トークンが有効かどうかを確認"""
        return not self.is_used and not self.is_expired()