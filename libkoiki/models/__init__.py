# src/models/__init__.py
# このファイルは Alembic がモデルを検出するためにインポートします。
# 新しいモデルを追加したら、ここにもインポートを追加してください。

from libkoiki.db.base import Base # SQLAlchemy Base をインポート
from .user import UserModel
from .role import RoleModel
from .permission import PermissionModel
from .associations import user_roles, role_permissions
from .todo import TodoModel # ★ ToDo モデルをインポート ★

# __all__ を定義しておくと、 from libkoiki.models import * でインポートされるものを明示できる
__all__ = [
    "Base",
    "UserModel",
    "RoleModel",
    "PermissionModel",
    "TodoModel", # ★ ToDo モデルを追加 ★
    "user_roles",
    "role_permissions",
]
