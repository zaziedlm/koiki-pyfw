from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator, validator


class BusinessClockMode(str, Enum):
    REALTIME = "REALTIME"
    OFFSET = "OFFSET"
    FROZEN = "FROZEN"


class BusinessClockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mode: BusinessClockMode
    base_timezone: str
    frozen_business_date: Optional[date] = None
    frozen_business_time: Optional[time] = None
    offset_days: int
    offset_minutes: int
    comment: Optional[str] = None
    version: int
    updated_by: str
    created_at: datetime
    updated_at: datetime


class BusinessClockUpdate(BaseModel):
    mode: BusinessClockMode = Field(..., description="Business clock mode")
    base_timezone: str = Field("Asia/Tokyo", description="IANA timezone name")
    frozen_business_date: Optional[date] = None
    frozen_business_time: Optional[time] = None
    offset_days: int = Field(0, ge=-3650, le=3650)
    offset_minutes: int = Field(0, ge=-1440, le=1440)
    comment: Optional[str] = None
    version: int = Field(..., ge=1)

    @validator("base_timezone")
    def validate_timezone(cls, value: str) -> str:
        from zoneinfo import ZoneInfo

        try:
            ZoneInfo(value)
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid timezone: {value}") from exc
        return value

    @model_validator(mode="after")
    def validate_mode_payload(cls, model: "BusinessClockUpdate") -> "BusinessClockUpdate":
        if model.mode == BusinessClockMode.FROZEN:
            if model.frozen_business_date is None or model.frozen_business_time is None:
                raise ValueError(
                    "frozen_business_date and frozen_business_time are required for FROZEN mode"
                )
        else:
            if model.frozen_business_date is not None or model.frozen_business_time is not None:
                raise ValueError(
                    "frozen business date/time must be omitted unless mode is FROZEN"
                )
            model.frozen_business_date = None
            model.frozen_business_time = None

        if model.mode == BusinessClockMode.REALTIME:
            model.offset_days = 0
            model.offset_minutes = 0
        return model


@dataclass(slots=True)
class BusinessClockState:
    mode: BusinessClockMode
    base_timezone: str
    frozen_business_date: Optional[date]
    frozen_business_time: Optional[time]
    offset_days: int
    offset_minutes: int
