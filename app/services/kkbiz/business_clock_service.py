from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kkbiz import BusinessClock
from app.repositories.kkbiz import BusinessClockRepository
from app.schemas.kkbiz import (
    BusinessClockMode,
    BusinessClockState,
    BusinessClockUpdate,
)
from libkoiki.core.transaction import transactional
from libkoiki.db.session import AsyncSessionFactory
from libkoiki.models.user import UserModel


class BusinessClockService:
    """
    Business clock domain service.
    """

    def __init__(self) -> None:
        self.repository = BusinessClockRepository()

    async def kkbiz_get_clock(self, db: AsyncSession) -> BusinessClock:
        self.repository.set_session(db)
        clock = await self.repository.get_singleton()
        if clock is None:
            clock = await self._kkbiz_init_clock(db)
        return clock

    @transactional
    async def kkbiz_update_clock(
        self,
        update_payload: BusinessClockUpdate,
        current_user: UserModel,
        db: AsyncSession,
    ) -> BusinessClock:
        self.repository.set_session(db)
        clock = await self.repository.get_for_update()
        if clock is None:
            clock = await self._kkbiz_init_clock(db, lock_for_update=True)

        if clock.version != update_payload.version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Business clock was updated by another request.",
            )

        now_utc = self.kkbiz_real_now_utc()

        ZoneInfo(update_payload.base_timezone)

        clock.mode = update_payload.mode.value
        clock.base_timezone = update_payload.base_timezone

        if update_payload.mode == BusinessClockMode.FROZEN:
            clock.frozen_business_date = update_payload.frozen_business_date
            clock.frozen_business_time = update_payload.frozen_business_time
            clock.offset_days = 0
            clock.offset_minutes = 0
        elif update_payload.mode == BusinessClockMode.OFFSET:
            clock.frozen_business_date = None
            clock.frozen_business_time = None
            clock.offset_minutes = update_payload.offset_minutes
            clock.offset_days = update_payload.offset_days
        else:
            clock.frozen_business_date = None
            clock.frozen_business_time = None
            clock.offset_minutes = 0
            clock.offset_days = 0

        clock.comment = update_payload.comment
        clock.version += 1
        clock.updated_by = current_user.username
        clock.updated_at = now_utc

        self.repository.db.add(clock)
        await self.repository.db.flush()
        await self.repository.db.refresh(clock)

        return clock

    def kkbiz_real_now_utc(self) -> datetime:
        return datetime.now(timezone.utc)

    def kkbiz_compute_business_now(self, state: BusinessClockState) -> datetime:
        zone = ZoneInfo(state.base_timezone)

        if state.mode == BusinessClockMode.REALTIME:
            return self.kkbiz_real_now_utc().astimezone(zone)

        if state.mode == BusinessClockMode.OFFSET:
            base_local = self.kkbiz_real_now_utc().astimezone(zone)
            shifted = base_local + timedelta(minutes=state.offset_minutes)
            shifted = shifted + timedelta(days=state.offset_days)
            return shifted

        if state.frozen_business_date is None or state.frozen_business_time is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Frozen mode requires date and time.",
            )

        frozen_dt = datetime.combine(
            state.frozen_business_date,
            state.frozen_business_time,
            tzinfo=zone,
        )
        return frozen_dt

    async def kkbiz_business_now(self, db: Optional[AsyncSession] = None) -> datetime:
        if db is not None:
            clock = await self.kkbiz_get_clock(db)
            return self.kkbiz_compute_business_now(self._kkbiz_to_state(clock))

        if AsyncSessionFactory is None:
            raise RuntimeError("AsyncSessionFactory is not initialized.")

        async with AsyncSessionFactory() as session:
            clock = await self.kkbiz_get_clock(session)
            return self.kkbiz_compute_business_now(self._kkbiz_to_state(clock))

    async def kkbiz_business_today(self, db: Optional[AsyncSession] = None):
        business_now = await self.kkbiz_business_now(db=db)
        return business_now.date()

    def _kkbiz_to_state(self, clock: BusinessClock) -> BusinessClockState:
        return BusinessClockState(
            mode=BusinessClockMode(clock.mode),
            base_timezone=clock.base_timezone,
            frozen_business_date=clock.frozen_business_date,
            frozen_business_time=clock.frozen_business_time,
            offset_days=clock.offset_days,
            offset_minutes=clock.offset_minutes,
        )

    async def _kkbiz_init_clock(
        self,
        db: AsyncSession,
        *,
        lock_for_update: bool = False,
    ) -> BusinessClock:
        default_clock = BusinessClock(
            mode=BusinessClockMode.REALTIME.value,
            base_timezone="Asia/Tokyo",
            offset_days=0,
            offset_minutes=0,
            version=1,
            updated_by="system",
        )
        db.add(default_clock)
        await db.flush()
        await db.refresh(default_clock)
        if lock_for_update:
            self.repository.set_session(db)
            default_clock = await self.repository.get_for_update() or default_clock
        return default_clock
