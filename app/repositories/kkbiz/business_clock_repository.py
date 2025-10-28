from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kkbiz import BusinessClock
from libkoiki.repositories.base import BaseRepository


class BusinessClockRepository(BaseRepository[BusinessClock, Any, Any]):
    """
    Repository for business clock singleton record.
    """

    def __init__(self) -> None:
        super().__init__(BusinessClock)

    async def get_singleton(self) -> Optional[BusinessClock]:
        stmt = select(BusinessClock).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_update(self) -> Optional[BusinessClock]:
        stmt = (
            select(BusinessClock)
            .with_for_update()
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
