# src/models/permission.py
from sqlalchemy import Column, String, Text
# from sqlalchemy.orm import relationship # Roleへの参照はRoleモデル側で定義

from libkoiki.db.base import Base

class PermissionModel(Base):
    __tablename__ = 'permissions' # テーブル名を明示的に指定 (CustomBaseを使うなら不要かも)

    name = Column(String(100), unique=True, index=True, nullable=False) # 権限名 (例: "read:users", "create:todos")
    description = Column(Text, nullable=True)

    # roles = relationship("RoleModel", secondary="role_permissions", back_populates="permissions") # RoleModelで定義

    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>"
