import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import TelegramWebhookEvent

logger = logging.getLogger(__name__)

STALE_EVENT_TIMEOUT = timedelta(minutes=10)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def claim_webhook_event(
    db: AsyncSession,
    update_id: int,
    webhook_type: str,
) -> bool:
    """
    Claim a Telegram update for processing.

    Returns True if this is a new event.
    Returns False if the event has already been registered.

    PostgreSQL's unique constraint prevents concurrent duplicate claims.
    """

    if webhook_type not in ("business", "group"):
        raise ValueError("Invalid webhook type")

    statement = (
        insert(TelegramWebhookEvent)
        .values(
            update_id=update_id,
            webhook_type=webhook_type,
            status="processing",
        )
        .on_conflict_do_nothing(constraint="uq_telegram_webhook_update_scope")
        .returning(TelegramWebhookEvent.id)
    )

    try:
        result = await db.execute(statement)
        event_id = result.scalar_one_or_none()
        await db.commit()

        return event_id is not None

    except Exception:
        await db.rollback()
        logger.exception(
            "Could not claim Telegram update %s (%s)",
            update_id,
            webhook_type,
        )
        raise


async def complete_webhook_event(
    db: AsyncSession,
    update_id: int,
    webhook_type: str,
) -> None:
    """Mark a successfully processed Telegram update as completed."""

    statement = (
        update(TelegramWebhookEvent)
        .where(
            TelegramWebhookEvent.update_id == update_id,
            TelegramWebhookEvent.webhook_type == webhook_type,
            TelegramWebhookEvent.status == "processing",
        )
        .values(
            status="completed",
            updated_at=utc_now(),
        )
    )

    await db.execute(statement)
    await db.commit()


async def fail_webhook_event(
    db: AsyncSession,
    update_id: int,
    webhook_type: str,
    error: str,
) -> None:
    """Mark an unsuccessful Telegram update as failed."""

    statement = (
        update(TelegramWebhookEvent)
        .where(
            TelegramWebhookEvent.update_id == update_id,
            TelegramWebhookEvent.webhook_type == webhook_type,
            TelegramWebhookEvent.status == "processing",
        )
        .values(
            status="failed",
            updated_at=utc_now(),
        )
    )

    try:
        await db.execute(statement)
        await db.commit()

        logger.error(
            "Telegram update %s (%s) failed: %s",
            update_id,
            webhook_type,
            error[:1000],
        )

    except Exception:
        await db.rollback()
        logger.exception(
            "Could not mark Telegram update %s as failed",
            update_id,
        )
        raise


async def recover_stale_webhook_events() -> int:
    """
    Mark webhook events abandoned for more than 10 minutes as failed.

    Events are not replayed automatically because their original
    Telegram message delivery outcome may be uncertain.
    """

    cutoff = utc_now() - STALE_EVENT_TIMEOUT

    statement = (
        update(TelegramWebhookEvent)
        .where(
            TelegramWebhookEvent.status == "processing",
            TelegramWebhookEvent.created_at <= cutoff,
        )
        .values(
            status="failed",
            updated_at=utc_now(),
        )
    )

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(statement)
            await db.commit()

            recovered_count = result.rowcount or 0

            if recovered_count:
                logger.warning(
                    "Recovered %s stale Telegram webhook events",
                    recovered_count,
                )

            return recovered_count

        except Exception:
            await db.rollback()
            logger.exception("Could not recover stale Telegram webhook events")
            raise
