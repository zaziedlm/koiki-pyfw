from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import AsyncGenerator
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.kkbiz import BusinessClock
from app.schemas.kkbiz import (
    BusinessClockMode,
    BusinessClockState,
    BusinessClockUpdate,
)
from app.services.kkbiz.business_clock_service import BusinessClockService
from libkoiki.db.base import Base


@pytest.fixture
def service():
    return BusinessClockService()


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an in-memory AsyncSession backed by SQLite for transactional tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        # Ensure the session is clean for the next test run
        if session.in_transaction():
            await session.rollback()

    await engine.dispose()


def test_kkbiz_compute_business_now_realtime(monkeypatch, service):
    fixed_utc = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(service, "kkbiz_real_now_utc", lambda: fixed_utc)

    state = BusinessClockState(
        mode=BusinessClockMode.REALTIME,
        base_timezone="Asia/Tokyo",
        frozen_business_date=None,
        frozen_business_time=None,
        offset_days=0,
        offset_minutes=0,
    )

    expected = fixed_utc.astimezone(ZoneInfo("Asia/Tokyo"))
    actual = service.kkbiz_compute_business_now(state)

    assert actual == expected


def test_kkbiz_compute_business_now_offset(monkeypatch, service):
    fixed_utc = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(service, "kkbiz_real_now_utc", lambda: fixed_utc)

    state = BusinessClockState(
        mode=BusinessClockMode.OFFSET,
        base_timezone="Asia/Tokyo",
        frozen_business_date=None,
        frozen_business_time=None,
        offset_days=1,
        offset_minutes=30,
    )

    zone = ZoneInfo("Asia/Tokyo")
    expected = fixed_utc.astimezone(zone) + timedelta(minutes=30) + timedelta(days=1)
    actual = service.kkbiz_compute_business_now(state)

    assert actual == expected


def test_kkbiz_compute_business_now_frozen(service):
    state = BusinessClockState(
        mode=BusinessClockMode.FROZEN,
        base_timezone="Asia/Tokyo",
        frozen_business_date=datetime(2025, 1, 5).date(),
        frozen_business_time=datetime(2025, 1, 5, 9, 0).time(),
        offset_days=0,
        offset_minutes=0,
    )

    actual = service.kkbiz_compute_business_now(state)
    zone = ZoneInfo("Asia/Tokyo")
    assert actual == datetime(2025, 1, 5, 9, 0, tzinfo=zone)


def test_business_clock_update_requires_frozen_fields():
    with pytest.raises(ValidationError):
        BusinessClockUpdate(
            mode=BusinessClockMode.FROZEN,
            base_timezone="Asia/Tokyo",
            version=1,
        )


@pytest.mark.asyncio
async def test_kkbiz_update_clock_frozen_happy_path(
    service: BusinessClockService, async_session: AsyncSession
):
    initial_clock = BusinessClock(
        id=1,
        mode=BusinessClockMode.REALTIME.value,
        base_timezone="Asia/Tokyo",
        offset_days=0,
        offset_minutes=0,
        version=1,
        updated_by="system",
    )

    async_session.add(initial_clock)
    await async_session.commit()
    await async_session.refresh(initial_clock)

    payload = BusinessClockUpdate(
        mode=BusinessClockMode.FROZEN,
        base_timezone="Asia/Tokyo",
        frozen_business_date=datetime(2025, 10, 28).date(),
        frozen_business_time=datetime(2025, 10, 28, 9, 0).time(),
        offset_days=0,
        offset_minutes=0,
        comment="switch frozen",
        version=1,
    )

    user = SimpleNamespace(username="admin")

    updated = await service.kkbiz_update_clock(
        payload, current_user=user, db=async_session
    )

    assert updated.mode == BusinessClockMode.FROZEN.value
    assert updated.frozen_business_date == payload.frozen_business_date
    assert updated.frozen_business_time == payload.frozen_business_time
    assert updated.version == 2
    assert updated.updated_by == user.username

    result = await async_session.execute(select(BusinessClock))
    stored_clock = result.scalar_one()

    assert stored_clock.mode == BusinessClockMode.FROZEN.value
    assert stored_clock.frozen_business_date == payload.frozen_business_date
    assert stored_clock.frozen_business_time == payload.frozen_business_time
    assert stored_clock.version == 2
    assert stored_clock.updated_by == user.username


@pytest.mark.asyncio
async def test_kkbiz_update_clock_version_mismatch(
    service: BusinessClockService, async_session: AsyncSession
):
    initial_clock = BusinessClock(
        id=1,
        mode=BusinessClockMode.REALTIME.value,
        base_timezone="Asia/Tokyo",
        offset_days=0,
        offset_minutes=0,
        version=2,
        updated_by="system",
    )

    async_session.add(initial_clock)
    await async_session.commit()
    await async_session.refresh(initial_clock)

    payload = BusinessClockUpdate(
        mode=BusinessClockMode.FROZEN,
        base_timezone="Asia/Tokyo",
        frozen_business_date=datetime(2025, 10, 29).date(),
        frozen_business_time=datetime(2025, 10, 29, 9, 0).time(),
        offset_days=0,
        offset_minutes=0,
        comment="stale version",
        version=1,
    )

    user = SimpleNamespace(username="admin")

    with pytest.raises(HTTPException) as exc_info:
        await service.kkbiz_update_clock(payload, current_user=user, db=async_session)

    assert getattr(exc_info.value, "status_code", None) == status.HTTP_409_CONFLICT
    result = await async_session.execute(select(BusinessClock))
    stored_clock = result.scalar_one()
    assert stored_clock.version == 2
    assert stored_clock.mode == BusinessClockMode.REALTIME.value


@pytest.mark.asyncio
async def test_kkbiz_update_clock_to_offset_resets_frozen_fields(
    service: BusinessClockService, async_session: AsyncSession
):
    initial_clock = BusinessClock(
        id=1,
        mode=BusinessClockMode.FROZEN.value,
        base_timezone="Asia/Tokyo",
        frozen_business_date=datetime(2025, 5, 1).date(),
        frozen_business_time=datetime(2025, 5, 1, 10, 0).time(),
        offset_days=0,
        offset_minutes=0,
        version=1,
        updated_by="system",
    )

    async_session.add(initial_clock)
    await async_session.commit()
    await async_session.refresh(initial_clock)

    payload = BusinessClockUpdate(
        mode=BusinessClockMode.OFFSET,
        base_timezone="Asia/Tokyo",
        frozen_business_date=None,
        frozen_business_time=None,
        offset_days=2,
        offset_minutes=90,
        comment="switch offset",
        version=1,
    )

    user = SimpleNamespace(username="editor")

    updated = await service.kkbiz_update_clock(
        payload, current_user=user, db=async_session
    )

    assert updated.mode == BusinessClockMode.OFFSET.value
    assert updated.offset_days == 2
    assert updated.offset_minutes == 90
    assert updated.frozen_business_date is None
    assert updated.frozen_business_time is None
    assert updated.version == 2
    assert updated.comment == "switch offset"
    assert updated.updated_by == user.username

    result = await async_session.execute(select(BusinessClock))
    stored_clock = result.scalar_one()
    assert stored_clock.mode == BusinessClockMode.OFFSET.value
    assert stored_clock.offset_days == 2
    assert stored_clock.offset_minutes == 90
    assert stored_clock.frozen_business_date is None
    assert stored_clock.frozen_business_time is None
    assert stored_clock.version == 2
    assert stored_clock.updated_by == user.username


@pytest.mark.asyncio
async def test_kkbiz_update_clock_to_realtime_resets_offsets(
    service: BusinessClockService, async_session: AsyncSession
):
    initial_clock = BusinessClock(
        id=1,
        mode=BusinessClockMode.OFFSET.value,
        base_timezone="Asia/Tokyo",
        frozen_business_date=None,
        frozen_business_time=None,
        offset_days=3,
        offset_minutes=120,
        version=1,
        updated_by="system",
    )

    async_session.add(initial_clock)
    await async_session.commit()
    await async_session.refresh(initial_clock)

    payload = BusinessClockUpdate(
        mode=BusinessClockMode.REALTIME,
        base_timezone="Asia/Tokyo",
        frozen_business_date=None,
        frozen_business_time=None,
        offset_days=0,
        offset_minutes=0,
        comment="back to realtime",
        version=1,
    )

    user = SimpleNamespace(username="editor")

    updated = await service.kkbiz_update_clock(
        payload, current_user=user, db=async_session
    )

    assert updated.mode == BusinessClockMode.REALTIME.value
    assert updated.offset_days == 0
    assert updated.offset_minutes == 0
    assert updated.frozen_business_date is None
    assert updated.frozen_business_time is None
    assert updated.version == 2
    assert updated.comment == "back to realtime"
    assert updated.updated_by == user.username

    result = await async_session.execute(select(BusinessClock))
    stored_clock = result.scalar_one()
    assert stored_clock.mode == BusinessClockMode.REALTIME.value
    assert stored_clock.offset_days == 0
    assert stored_clock.offset_minutes == 0
    assert stored_clock.frozen_business_date is None
    assert stored_clock.frozen_business_time is None
    assert stored_clock.version == 2
    assert stored_clock.updated_by == user.username


@pytest.mark.asyncio
async def test_kkbiz_update_clock_invalid_timezone(
    service: BusinessClockService, async_session: AsyncSession
):
    initial_clock = BusinessClock(
        id=1,
        mode=BusinessClockMode.REALTIME.value,
        base_timezone="Asia/Tokyo",
        offset_days=0,
        offset_minutes=0,
        version=1,
        updated_by="system",
    )

    async_session.add(initial_clock)
    await async_session.commit()
    await async_session.refresh(initial_clock)

    with pytest.raises(ValidationError):
        BusinessClockUpdate(
            mode=BusinessClockMode.REALTIME,
            base_timezone="Mars/Phobos",
            frozen_business_date=None,
            frozen_business_time=None,
            offset_days=0,
            offset_minutes=0,
            comment="invalid tz",
            version=1,
        )

    result = await async_session.execute(select(BusinessClock))
    stored_clock = result.scalar_one()
    assert stored_clock.base_timezone == "Asia/Tokyo"
    assert stored_clock.version == 1
