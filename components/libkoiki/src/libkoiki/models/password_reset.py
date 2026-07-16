# src/models/password_reset.py
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from libkoiki.db.base import Base


class PasswordResetModel(Base):
    """パスワードリセットトークンモデル"""

    __tablename__ = "koiki_password_reset_tokens"

    # BaseからのIDカラムを使用（手動定義不要）
    user_id = Column(
        Integer,
        ForeignKey("koiki_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, server_default=text("false"), nullable=False)
    # Baseからのcreated_atを使用（重複定義を削除）
    used_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6対応
    user_agent = Column(Text, nullable=True)

    # リレーションシップ
    user = relationship("UserModel", back_populates="password_reset_tokens")

    __table_args__ = (
        Index("ix_koiki_password_reset_tokens_user_id", user_id),
        Index(
            "ix_koiki_password_reset_tokens_active_user_id_expires_at",
            user_id,
            expires_at,
            postgresql_where=is_used.is_(False),
            sqlite_where=is_used.is_(False),
        ),
        Index("ix_koiki_password_reset_tokens_expires_at", expires_at),
    )

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
