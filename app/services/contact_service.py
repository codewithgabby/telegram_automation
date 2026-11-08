from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TelegramContact, ClientFollowUp

from app.services.engagement_event_service import record_engagement_event

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def get_contact(
    db: AsyncSession,
    telegram_user_id: int,
) -> TelegramContact | None:
    result = await db.execute(
        select(TelegramContact).where(
            TelegramContact.telegram_user_id == telegram_user_id
        )
    )
    return result.scalar_one_or_none()


async def create_contact(
    db: AsyncSession,
    telegram_user_id: int,
    chat_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
    business_connection_id: str | None = None,
) -> TelegramContact:
    now = utc_now()

    contact = TelegramContact(
        telegram_user_id=telegram_user_id,
        chat_id=chat_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        business_connection_id=business_connection_id,
        first_seen_at=now.replace(tzinfo=None),
        last_seen_at=now.replace(tzinfo=None),
    )

    db.add(contact)
    await db.flush()

    await record_engagement_event(
        db=db,
        contact_id=contact.id,
        event_type="new_enquiry",
        event_source="telegram",
        description="New client enquiry received through Telegram Business.",
    )
    await db.commit()
    await db.refresh(contact)

    return contact


async def get_locked_contact(
    db: AsyncSession,
    contact_id: int,
) -> TelegramContact | None:
    result = await db.execute(
        select(TelegramContact)
        .where(TelegramContact.id == contact_id)
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def begin_welcome_delivery(
    db: AsyncSession,
    contact: TelegramContact,
    business_connection_id: str,
) -> bool:
    locked_contact = await get_locked_contact(db, contact.id)

    if not locked_contact:
        return False

    if locked_contact.welcome_status != "pending":
        await db.commit()
        return False

    if locked_contact.welcome_sent_at is not None:
        locked_contact.welcome_status = "sent"
        await db.commit()
        return False

    locked_contact.welcome_status = "sending"
    locked_contact.business_connection_id = business_connection_id

    await db.commit()
    return True


async def complete_welcome_delivery(
    db: AsyncSession,
    contact: TelegramContact,
) -> ClientFollowUp:
    locked_contact = await get_locked_contact(db, contact.id)

    if not locked_contact:
        raise RuntimeError("Contact record not found.")

    if locked_contact.welcome_status == "sent":
        result = await db.execute(
            select(ClientFollowUp).where(ClientFollowUp.contact_id == locked_contact.id)
        )
        follow_up = result.scalar_one_or_none()

        await db.commit()

        if follow_up:
            return follow_up

        raise RuntimeError(
            "Welcome is marked sent, but its follow-up record is missing."
        )

    if locked_contact.welcome_status != "sending":
        await db.commit()
        raise RuntimeError(
            "Welcome delivery cannot be completed from its current status."
        )

    now = utc_now()

    locked_contact.welcome_status = "sent"
    locked_contact.welcome_sent_at = now

    result = await db.execute(
        select(ClientFollowUp).where(ClientFollowUp.contact_id == locked_contact.id)
    )
    follow_up = result.scalar_one_or_none()

    if not follow_up:
        follow_up = ClientFollowUp(
            contact_id=locked_contact.id,
            scheduled_at=now + timedelta(hours=12),
            status="pending",
        )
        db.add(follow_up)

        await record_engagement_event(
            db=db,
            contact_id=locked_contact.id,
            event_type="followup_scheduled",
            event_source="automation",
            description="A follow-up was scheduled for 12 hours after welcome delivery.",
        )

    await record_engagement_event(
        db=db,
        contact_id=locked_contact.id,
        event_type="welcome_delivered",
        event_source="telegram",
        description="Welcome message successfully delivered to the client.",
    )

    await db.commit()
    await db.refresh(follow_up)

    return follow_up


async def fail_welcome_delivery(
    db: AsyncSession,
    contact: TelegramContact,
    error: str,
) -> None:
    locked_contact = await get_locked_contact(db, contact.id)

    if not locked_contact:
        return

    if locked_contact.welcome_status == "sending":
        locked_contact.welcome_status = "failed"

    await db.commit()


async def record_incoming_message(
    db: AsyncSession,
    contact: TelegramContact,
) -> None:
    locked_contact = await get_locked_contact(db, contact.id)

    if not locked_contact:
        return

    now = utc_now()

    locked_contact.last_incoming_message_at = now
    locked_contact.last_seen_at = now.replace(tzinfo=None)

    await record_engagement_event(
        db=db,
        contact_id=locked_contact.id,
        event_type="client_replied",
        event_source="telegram",
        description="Client sent an incoming Telegram message.",
    )

    result = await db.execute(
        select(ClientFollowUp)
        .where(
            ClientFollowUp.contact_id == locked_contact.id,
            ClientFollowUp.status.in_(["pending", "processing"]),
        )
        .with_for_update()
    )

    follow_up = result.scalar_one_or_none()

    if follow_up:
        follow_up.status = "cancelled"
        follow_up.response = "replied"
        follow_up.last_error = "Cancelled because the contact replied."

    await db.commit()


async def update_payment_status(
    db: AsyncSession,
    contact: TelegramContact,
    payment_status: str,
) -> None:
    previous_status = contact.payment_status

    contact.payment_status = payment_status

    if previous_status != payment_status and payment_status == "paid":
        await record_engagement_event(
            db=db,
            contact_id=contact.id,
            event_type="payment_received",
            event_source="admin",
            previous_value=previous_status,
            new_value=payment_status,
            description="Client payment marked as received by admin.",
        )

    if payment_status == "paid":
        await cancel_pending_follow_up(db, contact.id)
    else:
        await db.commit()


async def update_session_status(
    db: AsyncSession,
    contact: TelegramContact,
    session_status: str,
) -> None:
    previous_status = contact.session_status

    contact.session_status = session_status

    if previous_status != session_status:
        if session_status == "booked":
            await record_engagement_event(
                db=db,
                contact_id=contact.id,
                event_type="session_booked",
                event_source="admin",
                previous_value=previous_status,
                new_value=session_status,
                description="Client strategy session marked as booked by admin.",
            )

        elif session_status == "completed":
            await record_engagement_event(
                db=db,
                contact_id=contact.id,
                event_type="session_completed",
                event_source="admin",
                previous_value=previous_status,
                new_value=session_status,
                description="Client strategy session marked as completed by admin.",
            )

    if session_status in ("booked", "completed"):
        await cancel_pending_follow_up(db, contact.id)
    else:
        await db.commit()


async def disable_follow_ups(
    db: AsyncSession,
    contact: TelegramContact,
) -> None:
    # The admin router already locks this contact.
    if contact.follow_up_enabled:
        await record_engagement_event(
            db=db,
            contact_id=contact.id,
            event_type="followups_disabled",
            event_source="admin",
            previous_value="enabled",
            new_value="disabled",
            description="Admin disabled automated follow-ups for this client.",
        )

    contact.follow_up_enabled = False

    await cancel_pending_follow_up(db, contact.id)


async def cancel_pending_follow_up(
    db: AsyncSession,
    contact_id: int,
) -> None:
    result = await db.execute(
        select(ClientFollowUp)
        .where(
            ClientFollowUp.contact_id == contact_id,
            ClientFollowUp.status.in_(["pending", "processing"]),
        )
        .with_for_update()
    )

    follow_up = result.scalar_one_or_none()

    if follow_up:
        follow_up.status = "cancelled"
        follow_up.last_error = "Cancelled by an administrative action."

    await db.commit()
