"""Portable vNext schema contracts that must hold in SQLite and PostgreSQL."""

from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from koiki_ref_app.bootstrap import bootstrap_orm
from koiki_ref_app.models.kkbiz import BusinessClock
from koiki_ref_app.models.saml_auth_flow import SamlAuthFlow
from libkoiki.db.base import Base
from libkoiki.models.login_attempt import LoginAttemptModel
from libkoiki.models.todo import TodoModel
from libkoiki.models.user import UserModel
from libkoiki.repositories.todo_repository import TodoRepository


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


async def _assert_check_rejected(session: AsyncSession, model: object) -> None:
    session.add(model)
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


@pytest.mark.asyncio
async def test_minimal_checks_accept_valid_values_in_sqlite(
    async_session: AsyncSession,
) -> None:
    user = UserModel(username="contract-user")
    async_session.add(user)
    await async_session.flush()

    async_session.add_all(
        [
            TodoModel(title="valid", owner_id=user.id, version=1),
            SamlAuthFlow(relay_nonce="valid-saml", status="authn_requested"),
            BusinessClock(
                id=1,
                mode="FROZEN",
                base_timezone="Asia/Tokyo",
                frozen_business_date=datetime(2026, 7, 15).date(),
                frozen_business_time=datetime(2026, 7, 15, 9, 0).time(),
                offset_days=0,
                offset_minutes=0,
                version=1,
                updated_by="contract-test",
            ),
        ]
    )
    await async_session.commit()


@pytest.mark.asyncio
async def test_minimal_checks_reject_invalid_values_in_sqlite(
    async_session: AsyncSession,
) -> None:
    user = UserModel(username="invalid-contract-user")
    async_session.add(user)
    await async_session.commit()

    await _assert_check_rejected(
        async_session,
        TodoModel(title="invalid version", owner_id=user.id, version=0),
    )
    await _assert_check_rejected(
        async_session,
        SamlAuthFlow(relay_nonce="invalid-status", status="unknown"),
    )
    await _assert_check_rejected(
        async_session,
        BusinessClock(
            id=2,
            mode="REALTIME",
            base_timezone="Asia/Tokyo",
            offset_days=0,
            offset_minutes=0,
            version=1,
            updated_by="contract-test",
        ),
    )
    await _assert_check_rejected(
        async_session,
        BusinessClock(
            id=1,
            mode="FROZEN",
            base_timezone="Asia/Tokyo",
            frozen_business_date=None,
            frozen_business_time=None,
            offset_days=0,
            offset_minutes=0,
            version=1,
            updated_by="contract-test",
        ),
    )


@pytest.mark.asyncio
async def test_mutable_entities_explicitly_advance_updated_at(
    async_session: AsyncSession,
) -> None:
    initial_time = datetime(2026, 7, 15, tzinfo=timezone.utc)
    user = UserModel(username="updated-at-user")
    async_session.add(user)
    await async_session.flush()
    todo = TodoModel(
        title="before update",
        owner_id=user.id,
        version=1,
        created_at=initial_time,
        updated_at=initial_time,
    )
    async_session.add(todo)
    await async_session.commit()

    repository = TodoRepository()
    repository.set_session(async_session)
    assert await repository.apply_versioned_update(
        todo.id,
        user.id,
        expected_version=1,
        update_data={"title": "after update"},
    ) == 1
    await async_session.commit()
    await async_session.refresh(todo)

    stored_updated_at = todo.updated_at.replace(tzinfo=timezone.utc)
    assert stored_updated_at > initial_time
    assert todo.version == 2


def test_append_only_and_association_tables_do_not_receive_updated_at() -> None:
    assert "updated_at" not in LoginAttemptModel.__table__.c
    assert "updated_at" not in Base.metadata.tables["koiki_user_roles"].c
    assert "updated_at" not in Base.metadata.tables["koiki_role_permissions"].c
