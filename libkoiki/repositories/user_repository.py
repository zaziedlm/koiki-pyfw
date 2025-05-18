# src/repositories/user_repository.py
from typing import Optional, Sequence # Sequence をインポート
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import structlog

from libkoiki.models.user import UserModel
from libkoiki.models.role import RoleModel # RoleModel をインポート
from libkoiki.models.permission import PermissionModel # PermissionModel をインポート
from libkoiki.repositories.base import BaseRepository
from libkoiki.schemas.user import UserCreate, UserUpdate # スキーマは直接使わない場合もある

logger = structlog.get_logger(__name__)

class UserRepository(BaseRepository[UserModel, UserCreate, UserUpdate]):
    """ユーザーリポジトリ実装"""

    def __init__(self):
        """コンストラクタでユーザーモデルを指定"""
        super().__init__(UserModel)

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """メールアドレスに基づいてユーザーを取得します"""
        logger.debug("Getting user by email", email=email)
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        # if user is None:
        #     logger.debug("User not found by email", email=email)
        return user

    async def get_user_with_roles_permissions(self, user_id: int) -> Optional[UserModel]:
        """
        ユーザー情報をロールと権限と共に Eager Loading して取得します。
        認証や権限チェックでの利用を想定。
        """
        logger.debug("Getting user with roles and permissions", user_id=user_id)
        stmt = (
            select(UserModel)
            .options(
                # roles をロードし、さらに roles に紐づく permissions もロードする
                selectinload(UserModel.roles).selectinload(RoleModel.permissions)
            )
            .where(UserModel.id == user_id)
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        # if user:
        #     logger.debug("User roles loaded", user_id=user_id, roles=[r.name for r in user.roles])
        #     if user.roles:
        #          perms = {p.name for r in user.roles for p in r.permissions}
        #          logger.debug("User permissions loaded", user_id=user_id, permissions=list(perms))
        # else:
        #      logger.debug("User not found for loading roles/permissions", user_id=user_id)
        return user

    # create, update, delete, get, get_multi は BaseRepository のものを使用

    # 必要に応じて特定のクエリメソッドを追加
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> Sequence[UserModel]:
        """アクティブなユーザーのみを取得します"""
        logger.debug("Getting active users", skip=skip, limit=limit)
        stmt = (
            select(self.model)
            .where(self.model.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.id)
        )
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        return users
