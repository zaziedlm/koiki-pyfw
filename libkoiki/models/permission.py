# src/models/permission.py
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libkoiki.db.base import Base


class PermissionModel(Base):
    __tablename__ = "permissions"

    # SQLAlchemy 2.0形式の型アノテーションに変更
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )  # 権限名 (例: "read:users", "create:todos")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # セキュリティ管理用の追加フィールド
    resource: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )  # リソース名 (例: "users", "todos", "security")
    action: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )  # アクション名 (例: "read", "write", "admin")

    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # RoleModelとの双方向リレーションシップを設定
    roles = relationship(
        "RoleModel", secondary="role_permissions", back_populates="permissions"
    )

    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}', resource='{self.resource}', action='{self.action}')>"

    @property
    def permission_scope(self) -> str:
        """権限のスコープを文字列で返す"""
        if self.resource and self.action:
            return f"{self.action}:{self.resource}"
        return self.name or "unknown"
