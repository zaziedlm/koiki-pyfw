import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.kkbiz import BusinessClockRead, BusinessClockUpdate
from app.services.kkbiz.business_clock_service import BusinessClockService
from libkoiki.api.dependencies import DBSessionDep, SuperUserDep

logger = structlog.get_logger(__name__)

router = APIRouter()

_service = BusinessClockService()


def get_business_clock_service() -> BusinessClockService:
    return _service


@router.get("", response_model=BusinessClockRead, status_code=status.HTTP_200_OK)
async def read_business_clock(
    db: DBSessionDep,
    service: BusinessClockService = Depends(get_business_clock_service),
) -> BusinessClockRead:
    clock = await service.kkbiz_get_clock(db)
    logger.info("Retrieved business clock settings", mode=clock.mode)
    return BusinessClockRead.from_orm(clock)


@router.post("", response_model=BusinessClockRead, status_code=status.HTTP_200_OK)
async def update_business_clock(
    payload: BusinessClockUpdate,
    db: DBSessionDep,
    current_user: SuperUserDep,
    service: BusinessClockService = Depends(get_business_clock_service),
) -> BusinessClockRead:
    if not current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user missing username.",
        )

    updated = await service.kkbiz_update_clock(
        payload, current_user=current_user, db=db
    )
    logger.info(
        "Business clock updated",
        mode=updated.mode,
        updated_by=updated.updated_by,
        version=updated.version,
    )
    return BusinessClockRead.from_orm(updated)


@router.get(
    "/current",
    status_code=status.HTTP_200_OK,
)
async def read_current_business_clock(
    db: DBSessionDep,
    service: BusinessClockService = Depends(get_business_clock_service),
) -> dict[str, object]:
    business_now = await service.kkbiz_business_now(db=db)
    business_today = business_now.date()
    real_now_utc = service.kkbiz_real_now_utc()
    delta = business_now.astimezone(real_now_utc.tzinfo) - real_now_utc
    logger.debug(
        "Business clock current time fetched",
        business_now=str(business_now),
        business_today=str(business_today),
        real_now=str(real_now_utc),
        delta=str(delta),
    )
    return {
        "business_now": business_now.isoformat(),
        "business_today": business_today.isoformat(),
        "real_now_utc": real_now_utc.isoformat().replace("+00:00", "Z"),
        "offset_minutes": int(delta.total_seconds() / 60),
    }
