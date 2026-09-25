from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TelegramContact


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
) -> TelegramContact:
    contact = TelegramContact(
        telegram_user_id=telegram_user_id,
        chat_id=chat_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        first_seen_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
    )

    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    return contact