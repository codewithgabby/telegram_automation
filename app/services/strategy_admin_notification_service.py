import asyncio
import logging

from datetime import datetime, timedelta, timezone

from sqlalchemy import case, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import AsyncSessionLocal
from app.models import StrategyAdminNotification
from app.services.strategy_admin_telegram_service import (
    send_strategy_admin_message,
)

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 10
BATCH_SIZE = 10
LOCK_TIMEOUT = timedelta(minutes=15)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def queue_admin_notification(
    db,
    event_key: str,
    event_type: str,
    message: str,
    available_at: datetime | None = None,
) -> bool:
    """Queue a notification within the caller's database transaction."""

    if not event_key or len(event_key) > 150:
        raise ValueError("Invalid administrator notification event key.")

    if not event_type or len(event_type) > 60:
        raise ValueError("Invalid administrator notification event type.")

    if not message or len(message) > 4000:
        raise ValueError("Notification message must be 1–4000 characters.")

    scheduled_at = available_at or utc_now()

    if scheduled_at.tzinfo is None or scheduled_at.utcoffset() is None:
        raise ValueError("Notification availability time must be timezone-aware.")

    statement = (
        pg_insert(StrategyAdminNotification)
        .values(
            event_key=event_key,
            event_type=event_type,
            message=message,
            status="pending",
            attempts=0,
            max_attempts=3,
            available_at=scheduled_at,
        )
        .on_conflict_do_nothing(
            index_elements=["event_key"],
        )
    )

    result = await db.execute(statement)

    return result.rowcount == 1

async def recover_stale_notifications() -> int:
    """
    Recover jobs left in processing after a worker crash.

    Jobs below their retry limit return to pending.
    Jobs that have exhausted their attempts become failed.
    """

    now = utc_now()
    stale_before = now - LOCK_TIMEOUT

    async with AsyncSessionLocal() as db:
        statement = (
            update(StrategyAdminNotification)
            .where(
                StrategyAdminNotification.status == "processing",
                StrategyAdminNotification.locked_at <= stale_before,
            )
            .values(
                status=case(
                    (
                        StrategyAdminNotification.attempts
                        < StrategyAdminNotification.max_attempts,
                        "pending",
                    ),
                    else_="failed",
                ),
                available_at=case(
                    (
                        StrategyAdminNotification.attempts
                        < StrategyAdminNotification.max_attempts,
                        now,
                    ),
                    else_=StrategyAdminNotification.available_at,
                ),
                locked_at=None,
                last_error=(
                    "Recovered stale processing job after worker interruption."
                ),
            )
        )

        result = await db.execute(statement)
        await db.commit()

        recovered_count = result.rowcount or 0

        if recovered_count:
            logger.warning(
                "Recovered %s stale administrator notification job(s).",
                recovered_count,
            )

        return recovered_count


async def claim_pending_notifications() -> list[int]:
    claimed_ids = []

    async with AsyncSessionLocal() as db:
        async with db.begin():
            now = utc_now()

            result = await db.execute(
                select(StrategyAdminNotification)
                .where(
                    StrategyAdminNotification.status == "pending",
                    StrategyAdminNotification.available_at <= now,
                    StrategyAdminNotification.attempts
                    < StrategyAdminNotification.max_attempts,
                )
                .order_by(
                    StrategyAdminNotification.available_at.asc(),
                    StrategyAdminNotification.id.asc(),
                )
                .limit(BATCH_SIZE)
                .with_for_update(skip_locked=True)
            )

            notifications = result.scalars().all()

            for notification in notifications:
                notification.status = "processing"
                notification.locked_at = now
                notification.attempts += 1

                claimed_ids.append(notification.id)

    return claimed_ids




async def deliver_notification(notification_id: int) -> None:
    async with AsyncSessionLocal() as db:
        notification = await db.get(
            StrategyAdminNotification,
            notification_id,
        )

        if not notification or notification.status != "processing":
            return

        message = notification.message

    try:
        await send_strategy_admin_message(message)

    except Exception as exc:
        logger.exception(
            "Administrator notification %s delivery failed.",
            notification_id,
        )

        async with AsyncSessionLocal() as db:
            notification = await db.get(
                StrategyAdminNotification,
                notification_id,
            )

            if not notification or notification.status != "processing":
                return

            notification.last_error = str(exc)[:1000]
            notification.locked_at = None

            if notification.attempts < notification.max_attempts:
                retry_seconds = min(
                    60 * (2 ** (notification.attempts - 1)),
                    900,
                )

                notification.status = "pending"
                notification.available_at = utc_now() + timedelta(seconds=retry_seconds)
            else:
                notification.status = "failed"

            await db.commit()

        return

    async with AsyncSessionLocal() as db:
        notification = await db.get(
            StrategyAdminNotification,
            notification_id,
        )

        if not notification or notification.status != "processing":
            return

        notification.status = "sent"
        notification.sent_at = utc_now()
        notification.locked_at = None
        notification.last_error = None

        await db.commit()

        logger.info(
            "Administrator notification %s sent successfully.",
            notification_id,
        )


async def process_pending_admin_notifications() -> None:
    await recover_stale_notifications()

    notification_ids = await claim_pending_notifications()

    for notification_id in notification_ids:
        await deliver_notification(notification_id)


async def strategy_admin_notification_scheduler_loop():
    logger.info("Strategy administrator notification scheduler started.")

    while True:
        try:
            await process_pending_admin_notifications()

        except Exception:
            logger.exception("Strategy administrator notification scheduler failed.")

        await asyncio.sleep(CHECK_INTERVAL)
