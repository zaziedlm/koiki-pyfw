from sqlalchemy import Column, ForeignKey, Integer, Table
from libkoiki.db.base import Base

# 既存のテーブル定義を修正（extend_existing=Trueを追加）
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    extend_existing=True  # 既存テーブルの再定義を許可
)

# role_permissionsも同様に修正
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
    extend_existing=True  # 既存テーブルの再定義を許可
)