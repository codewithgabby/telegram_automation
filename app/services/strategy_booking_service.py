import hashlib
import os
import secrets

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    StrategyBooking,
    StrategyCustomer,
    StrategyService,
)
from app.schemas.strategy_booking import StrategyBookingCreate
from app.services.strategy_admin_notification_service import (
    queue_admin_notification,
)


async def get_valid_booking_by_token(
    db: AsyncSession,
    raw_token: str,
) -> StrategyBooking:
    if not raw_token or len(raw_token) > 200:
        raise HTTPException(
            status_code=404,
            detail="This booking link is invalid or unavailable.",
        )

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    result = await db.execute(
        select(StrategyBooking).where(StrategyBooking.access_token_hash == token_hash)
    )

    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="This booking link is invalid or unavailable.",
        )

    now = datetime.now(timezone.utc)

    if booking.access_revoked_at is not None:
        raise HTTPException(
            status_code=403,
            detail="This booking link has been revoked. Please contact support.",
        )

    if booking.access_expires_at is None:
        raise HTTPException(
            status_code=403,
            detail="This booking link has expired. Please contact support.",
        )

    expires_at = booking.access_expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        raise HTTPException(
            status_code=403,
            detail="This booking link has expired. Please contact support.",
        )

    return booking


async def create_strategy_booking(
    db: AsyncSession,
    payload: StrategyBookingCreate,
) -> dict:
    result = await db.execute(
        select(StrategyService).where(
            StrategyService.code == payload.package_code,
            StrategyService.is_active.is_(True),
        )
    )

    package = result.scalar_one_or_none()

    if not package:
        raise HTTPException(
            status_code=404,
            detail="This consultation package is unavailable.",
        )

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    booking_reference = f"GJ-{secrets.token_hex(5).upper()}"

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=30)

    customer = StrategyCustomer(
        full_name=payload.full_name,
        email=payload.email,
        whatsapp=payload.whatsapp,
        country=payload.country,
        case_notes=payload.case_notes,
    )

    db.add(customer)
    await db.flush()

    booking = StrategyBooking(
        customer_id=customer.id,
        booking_reference=booking_reference,
        package_code=package.code,
        package_name=package.name,
        amount_ngn=package.price_ngn,
        session_count=package.session_count,
        status="pending_payment",
        access_token_hash=token_hash,
        access_expires_at=expires_at,
    )

    db.add(booking)

    try:
        await db.flush()

        notification_message = (
            "NEW STRATEGY SESSION BOOKING\n\n"
            f"Booking reference: {booking.booking_reference}\n"
            f"Customer: {customer.full_name}\n"
            f"Email: {customer.email}\n"
            f"WhatsApp: {customer.whatsapp}\n"
            f"Country: {customer.country}\n\n"
            f"Package: {booking.package_name}\n"
            f"Amount: ₦{booking.amount_ngn:,}\n"
            f"Sessions: {booking.session_count}\n"
            f"Status: {booking.status}\n\n"
            "Payment is awaiting submission."
        )

        await queue_admin_notification(
            db=db,
            event_key=f"strategy-booking-created:{booking.id}",
            event_type="booking_created",
            message=notification_message,
        )

        await db.commit()
        await db.refresh(booking)

    except Exception:
        await db.rollback()
        raise

    frontend_url = os.getenv(
        "FRONTEND_BASE_URL",
        "http://localhost:5173",
    ).rstrip("/")

    continuation_url = f"{frontend_url}/continue#token={raw_token}"

    return {
        "booking_reference": booking.booking_reference,
        "package_name": booking.package_name,
        "amount_ngn": booking.amount_ngn,
        "session_count": booking.session_count,
        "status": booking.status,
        "continuation_url": continuation_url,
        "message": "Your booking has been created successfully.",
    }


async def get_booking_by_access_token(
    db: AsyncSession,
    raw_token: str,
) -> dict:
    booking = await get_valid_booking_by_token(db, raw_token)

    return {
        "booking_reference": booking.booking_reference,
        "package_name": booking.package_name,
        "amount_ngn": booking.amount_ngn,
        "session_count": booking.session_count,
        "status": booking.status,
        "created_at": booking.created_at,
        "message": "Your booking was found successfully.",
    }
