from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from koiki_ref_app.bootstrap import bootstrap_orm
from koiki_ref_app.bootstrap.reference_seed import (
    REFERENCE_PERMISSIONS,
    REFERENCE_ROLES,
    seed_reference_data,
)
from koiki_ref_app.models.kkbiz import BusinessClock
from libkoiki.db.base import Base
from libkoiki.models.associations import role_permissions
from libkoiki.models.permission import PermissionModel
from libkoiki.models.role import RoleModel
from libkoiki.models.user import UserModel


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    bootstrap_orm()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_reference_seed_is_idempotent_and_never_creates_users(
    async_session: AsyncSession,
):
    first = await seed_reference_data(async_session)
    await async_session.commit()
    second = await seed_reference_data(async_session)
    await async_session.commit()

    assert first.permissions_created == len(REFERENCE_PERMISSIONS)
    assert first.roles_created == len(REFERENCE_ROLES)
    assert first.business_clock_created is True
    assert second.permissions_created == 0
    assert second.roles_created == 0
    assert second.role_permissions_created == 0
    assert second.business_clock_created is False
    assert (
        await async_session.scalar(select(func.count()).select_from(PermissionModel))
    ) == len(REFERENCE_PERMISSIONS)
    assert (
        await async_session.scalar(select(func.count()).select_from(RoleModel))
    ) == len(REFERENCE_ROLES)
    assert await async_session.scalar(select(func.count()).select_from(BusinessClock)) == 1
    assert await async_session.scalar(select(func.count()).select_from(role_permissions)) == 15
    assert await async_session.scalar(select(func.count()).select_from(UserModel)) == 0
