from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libkoiki.db.base import Base


class RoleModel(Base):
    __tablename__ = "roles"

    # SQLAlchemy 2.0形式の型アノテーションに変更
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # usersリレーションシップを追加
    users = relationship("UserModel", secondary="user_roles", back_populates="roles")

    # permissionsリレーションシップを追加（双方向リレーションシップ）
    permissions = relationship(
        "PermissionModel",
        secondary="role_permissions",
        back_populates="roles",
        lazy="joined",
    )
