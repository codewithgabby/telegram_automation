import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.telegram import TelegramUpdate
from app.services.contact_service import (
    create_contact,
    get_contact,
)
from app.services.telegram_service import send_business_message

load_dotenv()

TELEGRAM_WEBHOOK_SECRET = os.getenv(
    "TELEGRAM_WEBHOOK_SECRET"
)

router = APIRouter(
    prefix="/webhook",
    tags=["Telegram"],
)


WELCOME_MESSAGE = """Hello Sir/Ma, welcome.

If you’re here because you have a specific concern about your Canadian immigration plans, you can book a Personalized Strategy Session to have your situation reviewed more closely.

Whether it’s a document you want reviewed, a previous refusal, uncertainty about your pathway, or you simply need clarity on what to do next, you can get started here.

Book Your Strategy Session:
https://strategysession.netlify.app/

You’ll be able to choose the session that best fits your situation and follow the steps from there.
"""


@router.post("/telegram")
async def telegram_webhook(
    update: TelegramUpdate,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(
        default=None
    ),
):
    if x_telegram_bot_api_secret_token != TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook secret",
        )

    if not update.business_message:
        return {
            "ok": True,
            "message": "Update ignored",
        }

    business_message = update.business_message

    telegram_user_id = business_message.from_.id
    chat_id = business_message.chat.id

    contact = await get_contact(
        db=db,
        telegram_user_id=telegram_user_id,
    )

    # Existing contact → do not send welcome message again
    if contact:
        return {
            "ok": True,
            "message": "Existing contact",
        }

    # New contact → save them
    contact = await create_contact(
        db=db,
        telegram_user_id=telegram_user_id,
        chat_id=chat_id,
        username=business_message.from_.username,
        first_name=business_message.from_.first_name,
        last_name=business_message.from_.last_name,
    )

    # Send welcome message
    await send_business_message(
        business_connection_id=business_message.business_connection_id,
        chat_id=chat_id,
        text=WELCOME_MESSAGE,
    )

    return {
        "ok": True,
        "message": "New contact created and welcome message sent",
        "contact_id": contact.id,
    }