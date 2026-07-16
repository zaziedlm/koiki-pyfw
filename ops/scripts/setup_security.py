"""Create fixed-password development and E2E users.

Reference roles, permissions, and the business-clock singleton are seeded by
``python -m koiki_ref_app.bootstrap.reference_seed``.  This command adds only
development/test users and refuses production-like environments.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from koiki_ref_app.bootstrap import bootstrap_orm
from koiki_ref_app.bootstrap.reference_seed import seed_reference_data
from libkoiki.core.config import settings
from libkoiki.core.security import get_password_hash
from libkoiki.db.session import dispose_db_engine, get_db, init_db_engine
from libkoiki.models.associations import user_roles
from libkoiki.models.role import RoleModel
from libkoiki.models.user import UserModel
from ops.security.dev_users import INITIAL_USER_ROLES, TEST_USERS


ALLOWED_DEVELOPMENT_SEED_ENVS = frozenset({"development", "testing"})


def ensure_development_seed_environment(app_env: str) -> None:
    """Reject fixed-password seed execution outside isolated environments."""
    if app_env not in ALLOWED_DEVELOPMENT_SEED_ENVS:
        raise RuntimeError(
            "Development/E2E users may only be seeded when "
            f"APP_ENV is one of {sorted(ALLOWED_DEVELOPMENT_SEED_ENVS)}; got {app_env!r}."
        )


async def cleanup_existing_test_users(session: AsyncSession) -> int:
    """Remove only the known development users before recreating them."""
    emails = [user["email"] for user in TEST_USERS]
    usernames = [user["username"] for user in TEST_USERS]
    users = list(
        (
            await session.scalars(
                select(UserModel).where(
                    or_(UserModel.email.in_(emails), UserModel.username.in_(usernames))
                )
            )
        ).all()
    )
    for user in users:
        await session.delete(user)
    await session.flush()
    return len(users)


async def seed_development_users(session: AsyncSession) -> int:
    """Create fixed-password users after reference roles have been seeded."""
    await cleanup_existing_test_users(session)
    created = 0
    for user_data in TEST_USERS:
        user = UserModel(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            is_superuser=user_data["is_superuser"],
            is_active=user_data["is_active"],
        )
        session.add(user)
        await session.flush()
        for role_name in INITIAL_USER_ROLES[user_data["email"]]:
            role = await session.scalar(
                select(RoleModel).where(RoleModel.name == role_name)
            )
            if role is None:
                raise RuntimeError(f"Reference role is missing: {role_name}")
            await session.execute(
                user_roles.insert().values(user_id=user.id, role_id=role.id)
            )
        created += 1
    await session.flush()
    return created


async def setup_development_security_data() -> None:
    """Seed reference data plus development users in one transaction."""
    ensure_development_seed_environment(settings.APP_ENV)
    bootstrap_orm()
    init_db_engine()
    try:
        async for session in get_db():
            try:
                reference_result = await seed_reference_data(session)
                user_count = await seed_development_users(session)
                await session.commit()
                print(
                    "development security seed complete "
                    f"(reference_permissions={reference_result.permissions_created}, "
                    f"reference_roles={reference_result.roles_created}, users={user_count})"
                )
                return
            except Exception:
                await session.rollback()
                raise
    finally:
        await dispose_db_engine()


if __name__ == "__main__":
    asyncio.run(setup_development_security_data())
