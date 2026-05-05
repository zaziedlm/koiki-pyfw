"""SSO連携リポジトリの共通型定義。"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class SSOLinkRecord:
    """サービス層が参照する `user_sso` 互換フィールド。"""

    id: int
    user_id: int
    sso_subject_id: str
    sso_provider: str
    sso_email: Optional[str] = None
    sso_display_name: Optional[str] = None
    created_at: Optional[datetime] = None
    last_sso_login: Optional[datetime] = None


@runtime_checkable
class SSOLinkRepository(Protocol):
    """SAML/OIDC サービスから利用するリポジトリ契約。"""

    def set_session(self, db: AsyncSession) -> None: ...

    async def get_by_sso_subject_id(
        self, sso_subject_id: str, sso_provider: str = "oidc"
    ) -> Optional[Any]: ...

    async def get_by_user_id(
        self, user_id: int, sso_provider: str = None
    ) -> list[Any]: ...

    async def create_sso_link(
        self,
        user_id: int,
        sso_subject_id: str,
        sso_provider: str = "oidc",
        sso_email: str = None,
        sso_display_name: str = None,
    ) -> Any: ...

    async def update_sso_login(
        self, user_sso_id: int, sso_email: str = None, sso_display_name: str = None
    ) -> Optional[Any]: ...

    async def find_or_create_sso_link(
        self,
        user_id: int,
        sso_subject_id: str,
        sso_provider: str = "oidc",
        sso_email: str = None,
        sso_display_name: str = None,
    ) -> tuple[Any, bool]: ...

    async def get_recent_sso_logins(
        self, limit: int = 10, sso_provider: str = None
    ) -> list[Any]: ...
