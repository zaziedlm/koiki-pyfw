from sqlalchemy import Boolean, Column, String, text
from sqlalchemy.orm import relationship

from libkoiki.db.base import Base
from libkoiki.models.associations import user_roles

class UserModel(Base):
    __tablename__ = "koiki_users"

    # BaseからのIDカラムを使用（手動定義不要）
    username = Column(
        String(50), unique=True, nullable=False
    )  # ユーザー名追加
    email = Column(String, unique=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True, server_default=text("true"), nullable=False)
    is_superuser = Column(Boolean, default=False, server_default=text("false"), nullable=False)

    # todos = relationship("TodoModel", back_populates="user")
    todos = relationship(
        "TodoModel", back_populates="owner", cascade="all, delete-orphan"
    )
    # ロールとの関係
    roles = relationship("RoleModel", secondary=user_roles, back_populates="users")
    # リフレッシュトークンとの関係
    refresh_tokens = relationship(
        "RefreshTokenModel", back_populates="user", cascade="all, delete-orphan"
    )
    # パスワードリセットトークンとの関係
    password_reset_tokens = relationship(
        "PasswordResetModel", back_populates="user", cascade="all, delete-orphan"
    )
    # ログイン試行履歴との関係
    login_attempts = relationship(
        "LoginAttemptModel", back_populates="user", cascade="all, delete-orphan"
    )
