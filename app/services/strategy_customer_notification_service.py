import asyncio
import logging

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert

from app.database import AsyncSessionLocal
from app.models import (
    StrategyCustomerNotification,
    StrategyTelegramLink,
    TelegramContact,
)
from app.services.telegram_service import send_business_message

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 10
BATCH_SIZE = 10
LOCK_TIMEOUT = timedelta(minutes=15)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def queue_customer_notification(
    db,
    customer_id: int,
    event_key: str,
    event_type: str,
    message: str,
    available_at: datetime | None = None,
) -> None:
    if not event_key or len(event_key) > 150:
        raise ValueError("Customer notification event key is invalid.")

    if not event_type or len(event_type) > 60:
        raise ValueError("Customer notification event type is invalid.")

    if not message or len(message) > 4000:
        raise ValueError("Customer notification message is invalid.")

    scheduled_at = available_at or utc_now()

    if scheduled_at.tzinfo is None:
        raise ValueError("Notification time must include a timezone.")

    statement = (
        insert(StrategyCustomerNotification)
        .values(
            customer_id=customer_id,
            event_key=event_key,
            event_type=event_type,
            message=message,
            status="pending",
            attempts=0,
            max_attempts=3,
            available_at=scheduled_at,
        )
        .on_conflict_do_nothing(index_elements=["event_key"])
    )

    await db.execute(statement)


async def recover_stale_customer_notifications(db) -> None:
    now = utc_now()
    stale_before = now - LOCK_TIMEOUT

    await db.execute(
        update(StrategyCustomerNotification)
        .where(
            StrategyCustomerNotification.status == "processing",
            StrategyCustomerNotification.locked_at < stale_before,
        )
        .values(
            status="pending",
            locked_at=None,
            available_at=now,
            last_error="Recovered stale notification lock.",
        )
    )

    await db.commit()


async def claim_customer_notifications(db) -> list[int]:
    now = utc_now()

    result = await db.execute(
        select(StrategyCustomerNotification)
        .where(
            StrategyCustomerNotification.status == "pending",
            StrategyCustomerNotification.available_at <= now,
            StrategyCustomerNotification.attempts
            < StrategyCustomerNotification.max_attempts,
        )
        .order_by(
            StrategyCustomerNotification.available_at,
            StrategyCustomerNotification.id,
        )
        .limit(BATCH_SIZE)
        .with_for_update(skip_locked=True)
    )

    notifications = result.scalars().all()

    claimed_ids = []

    for notification in notifications:
        notification.status = "processing"
        notification.locked_at = now
        notification.attempts += 1
        claimed_ids.append(notification.id)

    await db.commit()

    return claimed_ids


async def get_customer_delivery_target(
    db,
    customer_id: int,
):
    result = await db.execute(
        select(TelegramContact)
        .join(
            StrategyTelegramLink,
            StrategyTelegramLink.telegram_contact_id == TelegramContact.id,
        )
        .where(
            StrategyTelegramLink.customer_id == customer_id,
            StrategyTelegramLink.revoked_at.is_(None),
        )
    )

    return result.scalar_one_or_none()


async def deliver_customer_notification(
    db,
    notification_id: int,
) -> None:
    notification = await db.get(
        StrategyCustomerNotification,
        notification_id,
    )

    if not notification or notification.status != "processing":
        return

    contact = await get_customer_delivery_target(
        db,
        notification.customer_id,
    )

    if not contact:
        # Keep the notification queued until the customer links Telegram.
        notification.status = "pending"
        notification.locked_at = None
        notification.attempts = max(0, notification.attempts - 1)
        notification.available_at = utc_now() + timedelta(minutes=5)
        notification.last_error = "Customer Telegram account is not linked."

        await db.commit()
        return

    if not contact.business_connection_id or not contact.chat_id:
        notification.status = "pending"
        notification.locked_at = None
        notification.attempts = max(0, notification.attempts - 1)
        notification.available_at = utc_now() + timedelta(minutes=5)
        notification.last_error = "Telegram Business delivery details unavailable."

        await db.commit()
        return

    try:
        await send_business_message(
            business_connection_id=contact.business_connection_id,
            chat_id=contact.chat_id,
            text=notification.message,
        )

        notification.status = "sent"
        notification.sent_at = utc_now()
        notification.locked_at = None
        notification.last_error = None

        await db.commit()

    except Exception as exc:
        logger.exception(
            "Customer notification %s delivery failed",
            notification_id,
        )

        notification.last_error = str(exc)[:1000]
        notification.locked_at = None

        if notification.attempts >= notification.max_attempts:
            notification.status = "failed"
        else:
            delay_seconds = min(
                60 * (2 ** (notification.attempts - 1)),
                900,
            )

            notification.status = "pending"
            notification.available_at = utc_now() + timedelta(seconds=delay_seconds)

        await db.commit()


async def process_customer_notification_batch() -> None:
    async with AsyncSessionLocal() as db:
        await recover_stale_customer_notifications(db)

        notification_ids = await claim_customer_notifications(db)

    for notification_id in notification_ids:
        async with AsyncSessionLocal() as db:
            await deliver_customer_notification(
                db,
                notification_id,
            )


async def strategy_customer_notification_scheduler_loop() -> None:
    logger.info("Strategy customer notification scheduler started")

    while True:
        try:
            await process_customer_notification_batch()

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception("Customer notification scheduler encountered an error")

        await asyncio.sleep(CHECK_INTERVAL)
