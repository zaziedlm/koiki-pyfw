"""app.models package.

このモジュールはアプリケーション内のモデルをまとめてインポートし、
libkoiki 側のモデルとアプリ側の SSO モデルを結合するための設定を行います。
"""

from sqlalchemy.orm import relationship

from libkoiki.models.login_attempt import LoginAttemptModel
from libkoiki.models.password_reset import PasswordResetModel
from libkoiki.models.permission import PermissionModel
from libkoiki.models.refresh_token import RefreshTokenModel
from libkoiki.models.role import RoleModel
from libkoiki.models.todo import TodoModel

# libkoiki の主要モデルをインポート
from libkoiki.models.user import UserModel

# アプリ内の SSO 関連モデル
from .user_sso import UserSSO

# UserModel に SSO のリレーションを追加
UserModel.sso_links = relationship(
    "UserSSO",
    back_populates="user",
    cascade="all, delete-orphan",
    lazy="select",
)

__all__ = [
    "UserModel",
    "TodoModel",
    "RoleModel",
    "PermissionModel",
    "RefreshTokenModel",
    "LoginAttemptModel",
    "PasswordResetModel",
    "UserSSO",
]
