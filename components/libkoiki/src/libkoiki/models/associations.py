from sqlalchemy import Column, ForeignKey, Index, Integer, Table
from libkoiki.db.base import Base

user_roles = Table(
    "koiki_user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("koiki_users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("koiki_roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "koiki_role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("koiki_roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id",
        Integer,
        ForeignKey("koiki_permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

Index("ix_koiki_user_roles_role_id", user_roles.c.role_id)
Index("ix_koiki_role_permissions_permission_id", role_permissions.c.permission_id)
