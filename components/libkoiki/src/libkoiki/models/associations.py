from sqlalchemy import Column, ForeignKey, Integer, Table
from libkoiki.db.base import Base

user_roles = Table(
    "koiki_user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("koiki_users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("koiki_roles.id"), primary_key=True),
)

role_permissions = Table(
    "koiki_role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("koiki_roles.id"), primary_key=True),
    Column(
        "permission_id",
        Integer,
        ForeignKey("koiki_permissions.id"),
        primary_key=True,
    ),
)
