"""SSO連携リポジトリの実装切替ファクトリ。"""

import os

import structlog

from app.repositories.user_sso_repository import UserSSORepository
from app.repositories.user_table_sso_repository import UserTableSSORepository

logger = structlog.get_logger(__name__)


def create_sso_link_repository():
    """
    環境変数で SSO連携リポジトリ実装を切替する。

    - `SSO_LINK_BACKEND=user_sso` (デフォルト): 標準 `user_sso` テーブル実装
    - `SSO_LINK_BACKEND=user_table`: 移行先 `user` テーブル実装
    """
    backend = os.getenv("SSO_LINK_BACKEND", "user_sso").strip().lower()

    if backend in {"user_sso", "default", "standard"}:
        logger.info("Using standard user_sso repository backend", backend=backend)
        return UserSSORepository()

    if backend in {"user_table", "user"}:
        logger.info("Using custom user-table repository backend", backend=backend)
        return UserTableSSORepository()

    raise ValueError(
        "Invalid SSO_LINK_BACKEND value. "
        "Allowed: user_sso, user_table. "
        f"actual={backend}"
    )
