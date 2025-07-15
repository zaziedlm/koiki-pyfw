# src/models/login_attempt.py
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from libkoiki.db.base import Base


class LoginAttemptModel(Base):
    """ログイン試行履歴モデル"""

    __tablename__ = "login_attempts"

    # BaseからのIDカラムを使用（手動定義不要）
    email = Column(
        String(255), nullable=False, index=True
    )  # ログイン試行されたメールアドレス
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )  # 存在する場合のユーザーID
    ip_address = Column(String(45), nullable=False, index=True)  # IPv6対応
    user_agent = Column(Text, nullable=True)
    is_successful = Column(Boolean, nullable=False, index=True)
    failure_reason = Column(
        String(100), nullable=True
    )  # 失敗理由（invalid_password, user_not_found, account_locked等）
    attempted_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    
    # Base class の created_at を attempted_at にマップ (semantically correct)
    created_at = attempted_at
    
    # updated_at は不要だが Base class 要件を満たすため None に設定
    updated_at = None

    # リレーションシップ（ユーザーが削除された場合はuser_idがNULLになる）
    user = relationship("UserModel", back_populates="login_attempts")

    @classmethod
    def get_lockout_window_start(cls, minutes: int = 15) -> datetime:
        """アカウントロックアウトの時間枠開始時刻を取得"""
        return datetime.now(timezone.utc) - timedelta(minutes=minutes)

    def is_within_window(self, minutes: int = 15) -> bool:
        """指定した時間枠内の試行かどうかを確認"""
        window_start = self.get_lockout_window_start(minutes)
        return self.attempted_at >= window_start
