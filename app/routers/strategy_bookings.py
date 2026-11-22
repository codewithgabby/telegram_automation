import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.strategy_booking import (
    StrategyBookingCreate,
    StrategyBookingCreateResponse,
)
from app.services.strategy_booking_service import (
    create_strategy_booking,
    get_booking_by_access_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/strategy/bookings",
    tags=["Strategy Session Bookings"],
)


class BookingAccessRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)


@router.post(
    "",
    response_model=StrategyBookingCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
    payload: StrategyBookingCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_strategy_booking(db, payload)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to create Strategy Session booking")
        raise HTTPException(
            status_code=500,
            detail="Unable to create your booking. Please try again.",
        )


@router.post("/continue")
async def continue_booking(
    payload: BookingAccessRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_booking_by_access_token(db, payload.token)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to validate Strategy Session continuation link")
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve this booking. Please try again.",
        )
