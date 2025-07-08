from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from libkoiki.db.base import Base

# user_roles テーブルの関連付け（多対多）
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id", Integer, ForeignKey("users.id"), primary_key=True
    ),  # 'user' ではなく 'users' を参照
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)


class UserModel(Base):
    __tablename__ = "users"  # テーブル名を "user" から "users" に変更

    # BaseからのIDカラムを使用（手動定義不要）
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

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
