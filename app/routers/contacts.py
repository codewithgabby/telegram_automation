from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import TelegramContact, ClientFollowUp
from app.routers.auth import get_current_admin
from app.services.contact_service import (
    update_payment_status,
    update_session_status,
    disable_follow_ups,
)

router = APIRouter(
    prefix="/admin/contacts",
    tags=["Contact Management"],
    dependencies=[Depends(get_current_admin)],
)


# =========================================================
# REQUEST SCHEMAS
# =========================================================


class PaymentUpdate(BaseModel):
    payment_status: str


class SessionUpdate(BaseModel):
    session_status: str


class FollowUpUpdate(BaseModel):
    enabled: bool


# =========================================================
# SHARED HELPERS
# =========================================================


async def get_locked_contact(
    db: AsyncSession,
    contact_id: int,
) -> TelegramContact:

    result = await db.execute(
        select(TelegramContact)
        .where(TelegramContact.id == contact_id)
        .with_for_update()
    )

    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    return contact


_UNSET = object()


async def build_contact_response(
    db: AsyncSession,
    contact: TelegramContact,
    follow_up=_UNSET,
):
    if follow_up is _UNSET:
        result = await db.execute(
            select(ClientFollowUp).where(ClientFollowUp.contact_id == contact.id)
        )
        follow_up = result.scalar_one_or_none()

    return {
        "id": contact.id,
        "telegram_user_id": contact.telegram_user_id,
        "chat_id": contact.chat_id,
        "username": contact.username,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "welcome_status": contact.welcome_status,
        "welcome_sent_at": contact.welcome_sent_at,
        "payment_status": contact.payment_status,
        "session_status": contact.session_status,
        "follow_up_enabled": contact.follow_up_enabled,
        "last_incoming_message_at": contact.last_incoming_message_at,
        "first_seen_at": contact.first_seen_at,
        "last_seen_at": contact.last_seen_at,
        "follow_up": (
            {
                "id": follow_up.id,
                "status": follow_up.status,
                "scheduled_at": follow_up.scheduled_at,
                "sent_at": follow_up.sent_at,
                "response": follow_up.response,
                "attempts": follow_up.attempts,
                "last_error": follow_up.last_error,
            }
            if follow_up
            else None
        ),
    }


# =========================================================
# LIST ALL CONTACTS
# =========================================================


@router.get("")
async def list_contacts(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TelegramContact, ClientFollowUp)
        .outerjoin(
            ClientFollowUp,
            ClientFollowUp.contact_id == TelegramContact.id,
        )
        .order_by(TelegramContact.first_seen_at.desc())
    )

    rows = result.all()

    response = []

    for contact, follow_up in rows:
        response.append(
            await build_contact_response(
                db=db,
                contact=contact,
                follow_up=follow_up,
            )
        )

    return response


# =========================================================
# GET CONTACT DETAILS
# =========================================================


@router.get("/{contact_id}")
async def get_contact_details(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
):
    contact = await db.get(TelegramContact, contact_id)

    if not contact:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    return await build_contact_response(
        db=db,
        contact=contact,
    )


# =========================================================
# UPDATE PAYMENT STATUS
# =========================================================


@router.patch("/{contact_id}/payment")
async def update_contact_payment(
    contact_id: int,
    data: PaymentUpdate,
    db: AsyncSession = Depends(get_db),
):
    if data.payment_status not in ("pending", "paid"):
        raise HTTPException(
            status_code=400,
            detail="Payment status must be pending or paid",
        )

    contact = await get_locked_contact(db, contact_id)

    await update_payment_status(
        db=db,
        contact=contact,
        payment_status=data.payment_status,
    )

    return {
        "message": "Payment status updated",
        "payment_status": contact.payment_status,
    }


# =========================================================
# UPDATE SESSION STATUS
# =========================================================


@router.patch("/{contact_id}/session")
async def update_contact_session(
    contact_id: int,
    data: SessionUpdate,
    db: AsyncSession = Depends(get_db),
):
    if data.session_status not in (
        "not_booked",
        "booked",
        "completed",
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid session status",
        )

    contact = await get_locked_contact(db, contact_id)

    await update_session_status(
        db=db,
        contact=contact,
        session_status=data.session_status,
    )

    return {
        "message": "Session status updated",
        "session_status": contact.session_status,
    }


# =========================================================
# ENABLE / DISABLE FOLLOW-UPS
# =========================================================


@router.patch("/{contact_id}/follow-ups")
async def update_contact_follow_ups(
    contact_id: int,
    data: FollowUpUpdate,
    db: AsyncSession = Depends(get_db),
):
    contact = await get_locked_contact(db, contact_id)

    if not data.enabled:
        await disable_follow_ups(db, contact)

    else:
        contact.follow_up_enabled = True
        await db.commit()

    return {
        "message": "Follow-up preference updated",
        "follow_up_enabled": contact.follow_up_enabled,
    }
