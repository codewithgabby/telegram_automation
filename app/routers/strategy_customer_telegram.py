import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.strategy_customer_telegram_service import (
    create_customer_telegram_link_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/strategy/bookings",
    tags=["Strategy Customer Telegram"],
)


class CustomerTelegramLinkRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)


@router.post("/telegram/link-token")
async def create_telegram_link_token(
    payload: CustomerTelegramLinkRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_customer_telegram_link_token(
            db=db,
            booking_access_token=payload.token,
        )

    except HTTPException:
        raise

    except Exception:
        await db.rollback()

        logger.exception("Failed to create customer Telegram linking token")

        raise HTTPException(
            status_code=500,
            detail="Unable to create your Telegram linking code. Please try again.",
        )
