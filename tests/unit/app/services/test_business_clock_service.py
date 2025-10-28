from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from app.models.kkbiz import BusinessClock
from app.repositories.kkbiz.business_clock_repository import BusinessClockRepository
from app.schemas.kkbiz import (
    BusinessClockMode,
    BusinessClockState,
    BusinessClockUpdate,
)
from app.services.kkbiz.business_clock_service import BusinessClockService


@pytest.fixture
def service():
    return BusinessClockService()


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
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BusinessClockUpdate(
            mode=BusinessClockMode.FROZEN,
            base_timezone="Asia/Tokyo",
            version=1,
        )


class _FakeBusinessClockRepository(BusinessClockRepository):
    def __init__(self, clock: BusinessClock):
        super().__init__()
        self._clock = clock

    async def get_for_update(self) -> BusinessClock:
        return self._clock


class _DummySession:
    def __init__(self) -> None:
        self.added = []
        self.flushed = False
        self.refreshed = None
        self.committed = False
        self._in_transaction = True

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flushed = True

    async def refresh(self, obj):
        self.refreshed = obj

    def in_transaction(self):
        return self._in_transaction

    async def commit(self):
        self.committed = True
        self._in_transaction = False

    async def rollback(self):
        self._in_transaction = False


@pytest.mark.asyncio
async def test_kkbiz_update_clock_frozen_happy_path():
    initial_clock = BusinessClock(
        id=1,
        mode=BusinessClockMode.REALTIME.value,
        base_timezone="Asia/Tokyo",
        offset_days=0,
        offset_minutes=0,
        version=1,
        updated_by="system",
    )

    service = BusinessClockService()
    fake_repo = _FakeBusinessClockRepository(initial_clock)
    service.repository = fake_repo

    session = _DummySession()

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

    updated = await service.kkbiz_update_clock(payload, current_user=user, db=session)

    assert updated.mode == BusinessClockMode.FROZEN.value
    assert updated.frozen_business_date == payload.frozen_business_date
    assert updated.frozen_business_time == payload.frozen_business_time
    assert updated.version == 2
    assert updated.updated_by == user.username

    assert session.committed is True
    assert session.flushed is True
    assert session.refreshed is updated
