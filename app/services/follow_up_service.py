import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import TelegramContact, ClientFollowUp
from app.services.telegram_service import (
    get_business_connection,
    send_business_message,
)
from app.services.webhook_event_service import recover_stale_webhook_events

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 60
MAX_ATTEMPTS = 3
PROCESSING_TIMEOUT = timedelta(minutes=10)
TELEGRAM_REPLY_WINDOW = timedelta(hours=24)

FOLLOW_UP_MESSAGE = """Hello Sir/Ma'am!

I hope you're doing well.

I'm just checking in regarding your earlier enquiry about our Canadian immigration strategy services.

If you still need guidance or would like to explore your options, I'm happy to help.

Would you like to know more about the Personalized Strategy Session?"""

FOLLOW_UP_KEYBOARD = {
    "inline_keyboard": [
        [
            {
                "text": "Yes, I'd like to know more",
                "callback_data": "followup_interested",
            }
        ],
        [{"text": "Not right now", "callback_data": "followup_not_now"}],
    ]
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_local_ineligibility_reason(
    contact: TelegramContact,
) -> str | None:
    now = utc_now()

    if not contact.follow_up_enabled:
        return "Follow-ups disabled"

    if contact.payment_status == "paid":
        return "Contact has paid"

    if contact.session_status in ("booked", "completed"):
        return "Consultation already booked or completed"

    if not contact.welcome_sent_at:
        return "Welcome message timestamp missing"

    if contact.welcome_status != "sent":
        return "Welcome message has not been confirmed as sent"

    if contact.last_incoming_message_at:
        if contact.last_incoming_message_at >= contact.welcome_sent_at:
            return "Contact has replied"

    if now - contact.welcome_sent_at >= TELEGRAM_REPLY_WINDOW:
        return "Telegram reply window expired"

    if not contact.business_connection_id:
        return "Business connection ID missing"

    return None


async def is_contact_eligible(
    contact: TelegramContact,
) -> tuple[bool, str]:
    reason = get_local_ineligibility_reason(contact)

    if reason:
        return False, reason

    try:
        connection = await get_business_connection(contact.business_connection_id)

        details = connection.get("result", {})

        if not details.get("is_enabled", False):
            return False, "Business connection disabled"

        rights = details.get("rights") or {}

        if not rights.get("can_reply", False):
            return False, "Telegram can_reply permission unavailable"

    except Exception:
        logger.exception(
            "Could not verify business connection for contact %s",
            contact.id,
        )
        return False, "Business connection verification failed"

    return True, "Eligible"


async def claim_due_follow_ups() -> list[int]:
    claimed_ids = []
    now = utc_now()
    stale_before = now - PROCESSING_TIMEOUT

    async with AsyncSessionLocal() as db:
        async with db.begin():

            # Do not resend jobs abandoned during a previous server run.
            # Their Telegram delivery outcome may be unknown.
            stale_result = await db.execute(
                select(ClientFollowUp)
                .where(
                    ClientFollowUp.status == "processing",
                    ClientFollowUp.updated_at <= stale_before,
                )
                .with_for_update(skip_locked=True)
            )

            stale_follow_ups = stale_result.scalars().all()

            for follow_up in stale_follow_ups:
                follow_up.status = "failed"
                follow_up.last_error = (
                    "Processing timed out. Delivery outcome is unknown; "
                    "automatic retry was prevented to avoid duplicate messages."
                )

            # Claim only new pending jobs.
            result = await db.execute(
                select(ClientFollowUp)
                .where(
                    ClientFollowUp.status == "pending",
                    ClientFollowUp.scheduled_at <= now,
                    ClientFollowUp.attempts < MAX_ATTEMPTS,
                )
                .order_by(ClientFollowUp.scheduled_at)
                .limit(20)
                .with_for_update(skip_locked=True)
            )

            follow_ups = result.scalars().all()

            for follow_up in follow_ups:
                follow_up.status = "processing"
                follow_up.attempts += 1
                claimed_ids.append(follow_up.id)

    return claimed_ids


async def process_follow_up(follow_up_id: int) -> None:
    async with AsyncSessionLocal() as db:

        # Read the contact ID first. The follow-up's contact_id is immutable.
        initial_result = await db.execute(
            select(ClientFollowUp.contact_id).where(ClientFollowUp.id == follow_up_id)
        )

        contact_id = initial_result.scalar_one_or_none()

        if contact_id is None:
            return

        # Always lock the contact first, followed by its follow-up.
        # This matches the locking order used by incoming messages
        # and administrative updates.
        contact_result = await db.execute(
            select(TelegramContact)
            .where(TelegramContact.id == contact_id)
            .with_for_update()
        )

        contact = contact_result.scalar_one_or_none()

        follow_up_result = await db.execute(
            select(ClientFollowUp)
            .where(ClientFollowUp.id == follow_up_id)
            .with_for_update()
        )

        follow_up = follow_up_result.scalar_one_or_none()

        if not follow_up or follow_up.status != "processing":
            await db.commit()
            return

        if not contact:
            follow_up.status = "cancelled"
            follow_up.last_error = "Contact record not found."
            await db.commit()
            return

        # Recheck every local eligibility condition while holding
        # both database locks.
        reason = get_local_ineligibility_reason(contact)

        if reason:
            follow_up.status = "skipped"
            follow_up.last_error = reason
            await db.commit()

            logger.info(
                "Follow-up %s skipped: %s",
                follow_up.id,
                reason,
            )
            return

        # Verify Telegram Business permissions immediately before sending.
        try:
            connection = await get_business_connection(contact.business_connection_id)

            details = connection.get("result", {})
            rights = details.get("rights") or {}

            if not details.get("is_enabled", False):
                raise RuntimeError("Business connection is disabled")

            if not rights.get("can_reply", False):
                raise RuntimeError("Telegram can_reply permission unavailable")

        except Exception as exc:
            follow_up.status = "skipped"
            follow_up.last_error = (
                "Business permission verification failed: " + str(exc)[:850]
            )

            await db.commit()

            logger.warning(
                "Follow-up %s skipped: Business permission unavailable",
                follow_up.id,
            )
            return

        # Keep the contact and follow-up locks until the delivery
        # outcome has been recorded.
        try:
            await send_business_message(
                business_connection_id=contact.business_connection_id,
                chat_id=contact.chat_id,
                text=FOLLOW_UP_MESSAGE,
                reply_markup=FOLLOW_UP_KEYBOARD,
            )

            follow_up.status = "sent"
            follow_up.sent_at = utc_now()
            follow_up.last_error = None

            await db.commit()

            logger.info(
                "Follow-up %s successfully sent to contact %s",
                follow_up.id,
                contact.id,
            )

        except Exception as exc:
            # Do not automatically retry an uncertain Telegram send.
            follow_up.status = "failed"
            follow_up.last_error = (
                "Telegram delivery could not be confirmed: " + str(exc)[:900]
            )

            await db.commit()

            logger.exception(
                "Follow-up %s delivery failed or could not be confirmed",
                follow_up.id,
            )


async def scheduler_loop():
    while True:
        try:
            await recover_stale_webhook_events()

            follow_up_ids = await claim_due_follow_ups()

            for follow_up_id in follow_up_ids:
                await process_follow_up(follow_up_id)

        except Exception:
            logger.exception("Follow-up scheduler error")

        await asyncio.sleep(CHECK_INTERVAL)
