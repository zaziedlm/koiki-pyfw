from typing import List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libkoiki.db.base import Base


class RoleModel(Base):
    __tablename__ = "koiki_roles"

    # SQLAlchemy 2.0形式の型アノテーションに変更
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # usersリレーションシップを追加
    users = relationship(
        "UserModel", secondary="koiki_user_roles", back_populates="roles"
    )

    # permissionsリレーションシップを追加（双方向リレーションシップ）
    permissions = relationship(
        "PermissionModel",
        secondary="koiki_role_permissions",
        back_populates="roles",
        lazy="joined",
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"

    @property
    def permission_names(self) -> List[str]:
        """このロールが持つ権限名のリストを返す"""
        return [perm.name for perm in self.permissions if perm.name]

    def has_permission(self, permission_name: str) -> bool:
        """指定された権限を持っているかチェック"""
        return permission_name in self.permission_names
