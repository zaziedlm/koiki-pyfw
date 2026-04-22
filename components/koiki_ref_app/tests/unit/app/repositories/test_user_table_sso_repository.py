from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from koiki_ref_app.repositories.sso_link_repository_factory import create_sso_link_repository
from koiki_ref_app.repositories.user_sso_repository import UserSSORepository
from koiki_ref_app.repositories.user_table_sso_repository import (
    UserTableSSORepository,
    _USER_TABLE,
)


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(_USER_TABLE.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        if session.in_transaction():
            await session.rollback()

    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_session(async_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    base_time = datetime(2026, 3, 5, 0, 0, tzinfo=timezone.utc)
    await async_session.execute(
        insert(_USER_TABLE),
        [
            {
                "user_id": 1,
                "user_name": "User One",
                "user_email": "one@example.com",
                "user_sso_provider": None,
                "user_sso_subject": None,
                "created_at": base_time,
                "updated_at": base_time,
                "is_deleted": False,
            },
            {
                "user_id": 2,
                "user_name": "User Two",
                "user_email": "two@example.com",
                "user_sso_provider": None,
                "user_sso_subject": None,
                "created_at": base_time,
                "updated_at": base_time + timedelta(minutes=1),
                "is_deleted": False,
            },
            {
                "user_id": 99,
                "user_name": "Deleted User",
                "user_email": "deleted@example.com",
                "user_sso_provider": "saml",
                "user_sso_subject": "deleted-subject",
                "created_at": base_time,
                "updated_at": base_time + timedelta(minutes=2),
                "is_deleted": True,
            },
        ],
    )
    await async_session.commit()
    yield async_session


@pytest.mark.asyncio
async def test_create_and_update_sso_link_on_user_table(seeded_session: AsyncSession):
    repo = UserTableSSORepository()
    repo.set_session(seeded_session)

    created = await repo.create_sso_link(
        user_id=1,
        sso_subject_id="subject-1",
        sso_provider="saml",
        sso_email="one-saml@example.com",
        sso_display_name="User One SAML",
    )
    assert created.id == 1
    assert created.user_id == 1
    assert created.sso_subject_id == "subject-1"
    assert created.sso_provider == "saml"
    assert created.sso_email == "one-saml@example.com"
    assert created.sso_display_name == "User One SAML"
    assert created.last_sso_login is not None

    found = await repo.get_by_sso_subject_id("subject-1", "saml")
    assert found is not None
    assert found.user_id == 1

    updated = await repo.update_sso_login(
        user_sso_id=1,
        sso_email="one-updated@example.com",
        sso_display_name="User One Updated",
    )
    assert updated is not None
    assert updated.sso_email == "one-updated@example.com"
    assert updated.sso_display_name == "User One Updated"

    row = (
        await seeded_session.execute(
            select(_USER_TABLE).where(_USER_TABLE.c.user_id == 1)
        )
    ).first()
    assert row is not None
    assert row._mapping["updated_by"] == "sso-system"


@pytest.mark.asyncio
async def test_create_sso_link_rejects_subject_conflict(seeded_session: AsyncSession):
    repo = UserTableSSORepository()
    repo.set_session(seeded_session)

    await repo.create_sso_link(
        user_id=1,
        sso_subject_id="same-subject",
        sso_provider="saml",
    )

    with pytest.raises(ValueError, match="already linked"):
        await repo.create_sso_link(
            user_id=2,
            sso_subject_id="same-subject",
            sso_provider="saml",
        )


@pytest.mark.asyncio
async def test_create_sso_link_inserts_user_row_when_missing(async_session: AsyncSession):
    repo = UserTableSSORepository()
    repo.set_session(async_session)

    created = await repo.create_sso_link(
        user_id=777,
        sso_subject_id="new-subject",
        sso_provider="saml",
        sso_email="new@example.com",
        sso_display_name="New User",
    )

    assert created.user_id == 777
    assert created.sso_subject_id == "new-subject"
    assert created.sso_provider == "saml"
    assert created.sso_email == "new@example.com"
    assert created.sso_display_name == "New User"

    row = (
        await async_session.execute(
            select(_USER_TABLE).where(_USER_TABLE.c.user_id == 777)
        )
    ).first()
    assert row is not None
    assert row._mapping["role_id"] == 5
    assert row._mapping["created_by"] == "sso-system"
    assert row._mapping["updated_by"] == "sso-system"


@pytest.mark.asyncio
async def test_get_recent_sso_logins_filters_deleted_and_orders(seeded_session: AsyncSession):
    repo = UserTableSSORepository()
    repo.set_session(seeded_session)

    await repo.create_sso_link(
        user_id=1,
        sso_subject_id="subject-u1",
        sso_provider="saml",
    )
    await repo.create_sso_link(
        user_id=2,
        sso_subject_id="subject-u2",
        sso_provider="saml",
    )

    recent = await repo.get_recent_sso_logins(limit=10, sso_provider="saml")
    assert len(recent) == 2
    assert {row.user_id for row in recent} == {1, 2}
    assert recent[0].last_sso_login >= recent[1].last_sso_login


def test_factory_switches_backend(monkeypatch):
    monkeypatch.setenv("SSO_LINK_BACKEND", "user_sso")
    backend = create_sso_link_repository()
    assert isinstance(backend, UserSSORepository)

    monkeypatch.setenv("SSO_LINK_BACKEND", "user_table")
    backend = create_sso_link_repository()
    assert isinstance(backend, UserTableSSORepository)

    monkeypatch.setenv("SSO_LINK_BACKEND", "invalid")
    with pytest.raises(ValueError, match="Invalid SSO_LINK_BACKEND"):
        create_sso_link_repository()
