"""`user` テーブルにSSO連携情報を保持する移行先向けリポジトリ。"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

import structlog
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    and_,
    desc,
    or_,
    select,
    insert,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.sso_link_repository import SSOLinkRecord

logger = structlog.get_logger(__name__)

DEFAULT_ROLE_ID = 5
DEFAULT_SSO_AUDIT_USER = "sso-system"


_USER_TABLE = Table(
    "user",
    MetaData(),
    Column("user_id", Integer),
    Column("user_name", String),
    Column("user_email", String),
    Column("role_id", Integer),
    Column("user_sso_provider", String),
    Column("user_sso_subject", String),
    Column("user_is_active", Boolean),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
    Column("created_by", String),
    Column("updated_by", String),
    Column("is_deleted", Boolean),
    quote=True,
)


@dataclass
class UserTableSSOLink(SSOLinkRecord):
    """`user` テーブル由来の SSO互換レコード。"""


class UserTableSSORepository:
    """
    `user_sso` の代わりに `user` テーブルの列を使う実装。

    - `id` は `user_id` を代用
    - `last_sso_login` は `updated_at` を代用
    """

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_session(self, db: AsyncSession):
        self._db = db

    @property
    def db(self) -> AsyncSession:
        if self._db is None:
            raise Exception(
                f"Database session not set for repository {self.__class__.__name__}"
            )
        return self._db

    @staticmethod
    def _not_deleted():
        return or_(
            _USER_TABLE.c.is_deleted.is_(None),
            _USER_TABLE.c.is_deleted.is_(False),
        )

    def _base_select(self):
        return (
            select(
                _USER_TABLE.c.user_id,
                _USER_TABLE.c.user_sso_subject.label("sso_subject_id"),
                _USER_TABLE.c.user_sso_provider.label("sso_provider"),
                _USER_TABLE.c.user_email.label("sso_email"),
                _USER_TABLE.c.user_name.label("sso_display_name"),
                _USER_TABLE.c.created_at,
                _USER_TABLE.c.updated_at.label("last_sso_login"),
            )
            .where(self._not_deleted())
            .where(_USER_TABLE.c.user_sso_subject.isnot(None))
            .where(_USER_TABLE.c.user_sso_provider.isnot(None))
        )

    @staticmethod
    def _to_link(row) -> UserTableSSOLink:
        m = row._mapping
        return UserTableSSOLink(
            id=m["user_id"],
            user_id=m["user_id"],
            sso_subject_id=m["sso_subject_id"],
            sso_provider=m["sso_provider"],
            sso_email=m["sso_email"],
            sso_display_name=m["sso_display_name"],
            created_at=m["created_at"],
            last_sso_login=m["last_sso_login"],
        )

    async def get_by_sso_subject_id(
        self, sso_subject_id: str, sso_provider: str = "oidc"
    ) -> Optional[UserTableSSOLink]:
        stmt = (
            self._base_select()
            .where(
                and_(
                    _USER_TABLE.c.user_sso_subject == sso_subject_id,
                    _USER_TABLE.c.user_sso_provider == sso_provider,
                )
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        row = result.first()
        return self._to_link(row) if row else None

    async def get_by_user_id(
        self, user_id: int, sso_provider: str = None
    ) -> List[UserTableSSOLink]:
        stmt = self._base_select().where(_USER_TABLE.c.user_id == user_id)
        if sso_provider:
            stmt = stmt.where(_USER_TABLE.c.user_sso_provider == sso_provider)

        stmt = stmt.order_by(desc(_USER_TABLE.c.updated_at))
        result = await self.db.execute(stmt)
        return [self._to_link(row) for row in result.fetchall()]

    async def _get_primary_link(
        self, user_id: int, sso_provider: Optional[str] = None
    ) -> Optional[UserTableSSOLink]:
        links = await self.get_by_user_id(user_id, sso_provider)
        if links:
            return links[0]
        if sso_provider is not None:
            fallback_links = await self.get_by_user_id(user_id, None)
            return fallback_links[0] if fallback_links else None
        return None

    async def _ensure_subject_unique(
        self, *, user_id: int, sso_subject_id: str, sso_provider: str
    ) -> None:
        stmt = (
            select(_USER_TABLE.c.user_id)
            .where(self._not_deleted())
            .where(_USER_TABLE.c.user_id != user_id)
            .where(_USER_TABLE.c.user_sso_subject == sso_subject_id)
            .where(_USER_TABLE.c.user_sso_provider == sso_provider)
            .limit(1)
        )
        result = await self.db.execute(stmt)
        conflict = result.scalar_one_or_none()
        if conflict is not None:
            raise ValueError(
                "SSO subject/provider is already linked to another user: "
                f"provider={sso_provider}, subject={sso_subject_id}"
            )

    async def create_sso_link(
        self,
        user_id: int,
        sso_subject_id: str,
        sso_provider: str = "oidc",
        sso_email: str = None,
        sso_display_name: str = None,
    ) -> UserTableSSOLink:
        await self._ensure_subject_unique(
            user_id=user_id,
            sso_subject_id=sso_subject_id,
            sso_provider=sso_provider,
        )

        now = datetime.now(timezone.utc)
        values = {
            "user_sso_provider": sso_provider,
            "user_sso_subject": sso_subject_id,
            "updated_at": now,  # last_sso_login 代用
            "updated_by": DEFAULT_SSO_AUDIT_USER,
        }
        if sso_email is not None:
            values["user_email"] = sso_email
        if sso_display_name is not None:
            values["user_name"] = sso_display_name

        stmt = (
            update(_USER_TABLE)
            .where(and_(_USER_TABLE.c.user_id == user_id, self._not_deleted()))
            .values(**values)
        )
        result = await self.db.execute(stmt)
        if result.rowcount == 0:
            # 移行先では user 行が既に存在する想定だが、
            # 検証環境では未作成のケースがあるためフォールバックで作成する。
            insert_values = {
                "user_id": user_id,
                "user_name": sso_display_name,
                "user_email": sso_email,
                "role_id": DEFAULT_ROLE_ID,
                "user_sso_provider": sso_provider,
                "user_sso_subject": sso_subject_id,
                "user_is_active": True,
                "created_at": now,
                "updated_at": now,
                "created_by": DEFAULT_SSO_AUDIT_USER,
                "updated_by": DEFAULT_SSO_AUDIT_USER,
                "is_deleted": False,
            }
            await self.db.execute(insert(_USER_TABLE).values(**insert_values))

        await self.db.flush()
        linked = await self._get_primary_link(user_id, sso_provider)
        if linked is None:
            raise ValueError(f"failed to load linked user row: user_id={user_id}")
        return linked

    async def update_sso_login(
        self, user_sso_id: int, sso_email: str = None, sso_display_name: str = None
    ) -> Optional[UserTableSSOLink]:
        # 互換性維持: user_sso_id を user_id として扱う
        current = await self._get_primary_link(user_sso_id, None)
        if not current:
            return None

        values = {
            "updated_at": datetime.now(timezone.utc),
            "updated_by": DEFAULT_SSO_AUDIT_USER,
        }
        if sso_email is not None:
            values["user_email"] = sso_email
        if sso_display_name is not None:
            values["user_name"] = sso_display_name

        stmt = (
            update(_USER_TABLE)
            .where(and_(_USER_TABLE.c.user_id == user_sso_id, self._not_deleted()))
            .values(**values)
        )
        await self.db.execute(stmt)
        await self.db.flush()
        return await self._get_primary_link(user_sso_id, current.sso_provider)

    async def find_or_create_sso_link(
        self,
        user_id: int,
        sso_subject_id: str,
        sso_provider: str = "oidc",
        sso_email: str = None,
        sso_display_name: str = None,
    ) -> tuple[UserTableSSOLink, bool]:
        existing_sso = await self.get_by_sso_subject_id(sso_subject_id, sso_provider)
        if existing_sso:
            await self.update_sso_login(
                existing_sso.id,
                sso_email=sso_email,
                sso_display_name=sso_display_name,
            )
            refreshed = await self.get_by_sso_subject_id(sso_subject_id, sso_provider)
            return (refreshed or existing_sso), False

        existing_links = await self.get_by_user_id(user_id, sso_provider)
        if existing_links:
            updated = await self.create_sso_link(
                user_id=user_id,
                sso_subject_id=sso_subject_id,
                sso_provider=sso_provider,
                sso_email=sso_email,
                sso_display_name=sso_display_name,
            )
            return updated, False

        created = await self.create_sso_link(
            user_id=user_id,
            sso_subject_id=sso_subject_id,
            sso_provider=sso_provider,
            sso_email=sso_email,
            sso_display_name=sso_display_name,
        )
        return created, True

    async def get_recent_sso_logins(
        self, limit: int = 10, sso_provider: str = None
    ) -> List[UserTableSSOLink]:
        stmt = self._base_select().where(_USER_TABLE.c.updated_at.isnot(None))
        if sso_provider:
            stmt = stmt.where(_USER_TABLE.c.user_sso_provider == sso_provider)
        stmt = stmt.order_by(desc(_USER_TABLE.c.updated_at)).limit(limit)
        result = await self.db.execute(stmt)
        return [self._to_link(row) for row in result.fetchall()]
