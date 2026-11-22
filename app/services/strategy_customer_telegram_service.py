import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    StrategyTelegramLink,
    StrategyTelegramLinkToken,
    TelegramContact,
)
from app.services.strategy_booking_service import get_valid_booking_by_token

LINK_TOKEN_EXPIRY_MINUTES = 15
LINK_CODE_PREFIX = "LINK-"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_customer_telegram_link_token(
    db: AsyncSession,
    booking_access_token: str,
) -> dict:
    booking = await get_valid_booking_by_token(
        db,
        booking_access_token,
    )

    existing_result = await db.execute(
        select(StrategyTelegramLink).where(
            StrategyTelegramLink.customer_id == booking.customer_id,
            StrategyTelegramLink.revoked_at.is_(None),
        )
    )

    existing_link = existing_result.scalar_one_or_none()

    if existing_link:
        return {
            "linked": True,
            "message": "Your Telegram account is already linked.",
        }

    now = utc_now()

    await db.execute(
        update(StrategyTelegramLinkToken)
        .where(
            StrategyTelegramLinkToken.customer_id == booking.customer_id,
            StrategyTelegramLinkToken.consumed_at.is_(None),
        )
        .values(expires_at=now)
    )

    raw_token = secrets.token_urlsafe(32)
    link_code = f"{LINK_CODE_PREFIX}{raw_token}"
    expires_at = now + timedelta(minutes=LINK_TOKEN_EXPIRY_MINUTES)

    token_record = StrategyTelegramLinkToken(
        booking_id=booking.id,
        customer_id=booking.customer_id,
        token_hash=hash_token(link_code),
        expires_at=expires_at,
    )

    db.add(token_record)

    await db.commit()

    return {
        "linked": False,
        "link_code": link_code,
        "expires_at": expires_at.isoformat(),
        "message": (
            "Open your existing Telegram Business conversation "
            "and send the linking code provided."
        ),
    }


async def consume_customer_telegram_link_code(
    db: AsyncSession,
    contact: TelegramContact,
    message_text: str,
) -> dict | None:
    code = message_text.strip()

    if not code.startswith(LINK_CODE_PREFIX):
        return None

    if len(code) > 150:
        return {
            "success": False,
            "message": "Invalid or expired linking code.",
        }

    result = await db.execute(
        select(StrategyTelegramLinkToken)
        .where(
            StrategyTelegramLinkToken.token_hash == hash_token(code),
            StrategyTelegramLinkToken.consumed_at.is_(None),
        )
        .with_for_update()
    )

    token_record = result.scalar_one_or_none()

    if not token_record:
        return {
            "success": False,
            "message": "Invalid or expired linking code.",
        }

    now = utc_now()
    expires_at = token_record.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        return {
            "success": False,
            "message": "This linking code has expired. Request a new one.",
        }

    link_result = await db.execute(
        select(StrategyTelegramLink)
        .where(StrategyTelegramLink.customer_id == token_record.customer_id)
        .with_for_update()
    )

    customer_link = link_result.scalar_one_or_none()

    if customer_link:
        customer_link.telegram_contact_id = contact.id
        customer_link.linked_at = now
        customer_link.revoked_at = None
    else:
        customer_link = StrategyTelegramLink(
            customer_id=token_record.customer_id,
            telegram_contact_id=contact.id,
            linked_at=now,
        )
        db.add(customer_link)

    token_record.consumed_at = now

    await db.commit()

    return {
        "success": True,
        "customer_id": token_record.customer_id,
        "message": "Your Telegram account has been linked successfully.",
    }
