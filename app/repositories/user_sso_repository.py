# app/repositories/user_sso_repository.py
"""
UserSSO リポジトリ

UserSSOモデルのデータアクセス層を実装
libkoikiのBaseRepositoryを継承し、SSO連携固有のクエリメソッドを提供
"""

from datetime import datetime
from typing import List, Optional

import structlog
from pydantic import BaseModel
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user_sso import UserSSO
from libkoiki.models.user import UserModel
from libkoiki.repositories.base import BaseRepository

logger = structlog.get_logger(__name__)


class UserSSORepository(BaseRepository[UserSSO, BaseModel, BaseModel]):
    """
    UserSSO リポジトリクラス

    SSO連携情報の永続化とクエリ操作を提供
    libkoikiのBaseRepositoryを継承し、標準的なCRUD操作に加えて
    SSO固有の検索・更新機能を実装
    """

    def __init__(self):
        super().__init__(UserSSO)

    async def get_by_sso_subject_id(
        self, sso_subject_id: str, sso_provider: str = "oidc"
    ) -> Optional[UserSSO]:
        """
        SSO識別子とプロバイダーでSSO連携情報を検索

        Args:
            sso_subject_id: SSOサービスでの一意識別子
            sso_provider: SSOプロバイダー名

        Returns:
            該当するUserSSOオブジェクト、見つからない場合はNone
        """
        logger.debug(
            "Searching SSO link by subject_id",
            sso_subject_id=sso_subject_id,
            sso_provider=sso_provider,
        )

        query = (
            select(UserSSO)
            .where(
                and_(
                    UserSSO.sso_subject_id == sso_subject_id,
                    UserSSO.sso_provider == sso_provider,
                )
            )
            .options(selectinload(UserSSO.user))
        )  # ユーザー情報も同時取得

        result = await self.session.execute(query)
        user_sso = result.scalar_one_or_none()

        if user_sso:
            logger.debug(
                "SSO link found", user_sso_id=user_sso.id, user_id=user_sso.user_id
            )
        else:
            logger.debug("SSO link not found")

        return user_sso

    async def get_by_user_id(
        self, user_id: int, sso_provider: str = None
    ) -> List[UserSSO]:
        """
        ユーザーIDでSSO連携情報を検索

        Args:
            user_id: ユーザーID
            sso_provider: SSOプロバイダー名（指定時はそのプロバイダーのみ）

        Returns:
            該当するUserSSOオブジェクトのリスト
        """
        logger.debug(
            "Searching SSO links by user_id", user_id=user_id, sso_provider=sso_provider
        )

        query = select(UserSSO).where(UserSSO.user_id == user_id)

        if sso_provider:
            query = query.where(UserSSO.sso_provider == sso_provider)

        query = query.order_by(desc(UserSSO.last_sso_login))

        result = await self.session.execute(query)
        user_ssos = result.scalars().all()

        logger.debug("Found SSO links", count=len(user_ssos), user_id=user_id)

        return list(user_ssos)

    async def create_sso_link(
        self,
        user_id: int,
        sso_subject_id: str,
        sso_provider: str = "oidc",
        sso_email: str = None,
        sso_display_name: str = None,
    ) -> UserSSO:
        """
        新しいSSO連携を作成

        Args:
            user_id: ユーザーID
            sso_subject_id: SSO識別子
            sso_provider: SSOプロバイダー名
            sso_email: SSO側のメールアドレス
            sso_display_name: SSO側の表示名

        Returns:
            作成されたUserSSOオブジェクト
        """
        logger.info(
            "Creating SSO link",
            user_id=user_id,
            sso_subject_id=sso_subject_id,
            sso_provider=sso_provider,
        )

        user_sso = UserSSO(
            user_id=user_id,
            sso_subject_id=sso_subject_id,
            sso_provider=sso_provider,
            sso_email=sso_email,
            sso_display_name=sso_display_name,
            last_sso_login=datetime.utcnow(),
        )

        created_user_sso = await self.create(user_sso)

        logger.info(
            "SSO link created", user_sso_id=created_user_sso.id, user_id=user_id
        )

        return created_user_sso

    async def update_sso_login(
        self, user_sso_id: int, sso_email: str = None, sso_display_name: str = None
    ) -> Optional[UserSSO]:
        """
        SSO連携の最終ログイン日時と情報を更新

        Args:
            user_sso_id: UserSSO ID
            sso_email: 更新するSSO側メールアドレス
            sso_display_name: 更新するSSO側表示名

        Returns:
            更新されたUserSSOオブジェクト、見つからない場合はNone
        """
        logger.debug("Updating SSO login info", user_sso_id=user_sso_id)

        user_sso = await self.get(user_sso_id)
        if not user_sso:
            logger.warning("SSO link not found for update", user_sso_id=user_sso_id)
            return None

        # ログイン日時更新
        user_sso.update_login_timestamp()

        # SSO情報更新
        if sso_email is not None or sso_display_name is not None:
            user_sso.update_sso_info(sso_email, sso_display_name)

        updated_user_sso = await self.update(user_sso)

        logger.info(
            "SSO login info updated",
            user_sso_id=updated_user_sso.id,
            user_id=updated_user_sso.user_id,
        )

        return updated_user_sso

    async def find_or_create_sso_link(
        self,
        user_id: int,
        sso_subject_id: str,
        sso_provider: str = "oidc",
        sso_email: str = None,
        sso_display_name: str = None,
    ) -> tuple[UserSSO, bool]:
        """
        SSO連携を検索し、存在しない場合は新規作成

        Args:
            user_id: ユーザーID
            sso_subject_id: SSO識別子
            sso_provider: SSOプロバイダー名
            sso_email: SSO側のメールアドレス
            sso_display_name: SSO側の表示名

        Returns:
            (UserSSOオブジェクト, 新規作成フラグ)
        """
        # まず既存のSSO連携を検索
        existing_sso = await self.get_by_sso_subject_id(sso_subject_id, sso_provider)

        if existing_sso:
            # 既存連携が見つかった場合は情報を更新
            await self.update_sso_login(
                existing_sso.id, sso_email=sso_email, sso_display_name=sso_display_name
            )
            return existing_sso, False

        # 見つからない場合は新規作成
        new_sso = await self.create_sso_link(
            user_id=user_id,
            sso_subject_id=sso_subject_id,
            sso_provider=sso_provider,
            sso_email=sso_email,
            sso_display_name=sso_display_name,
        )
        return new_sso, True

    async def get_recent_sso_logins(
        self, limit: int = 10, sso_provider: str = None
    ) -> List[UserSSO]:
        """
        最近のSSO ログインを取得

        Args:
            limit: 取得する最大件数
            sso_provider: SSOプロバイダー名（指定時はそのプロバイダーのみ）

        Returns:
            最近のSSO ログインのリスト
        """
        query = (
            select(UserSSO)
            .where(UserSSO.last_sso_login.isnot(None))
            .options(selectinload(UserSSO.user))
        )

        if sso_provider:
            query = query.where(UserSSO.sso_provider == sso_provider)

        query = query.order_by(desc(UserSSO.last_sso_login)).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())
