import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.telegram import TelegramUpdate, GroupMessage
from app.services.contact_service import (
    create_contact,
    get_contact,
)
from app.services.telegram_service import (
    get_business_connection,
    send_business_message,
)

from app.services.group_telegram_service import (
    get_group_chat_member,
    send_group_message,
)

from app.services.faq_service import find_matching_faqs

load_dotenv()

TELEGRAM_WEBHOOK_SECRET = os.getenv(
    "TELEGRAM_WEBHOOK_SECRET"
)

GROUP_TELEGRAM_WEBHOOK_SECRET = os.getenv("GROUP_TELEGRAM_WEBHOOK_SECRET")

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


GROUP_FAQ_REPLY = """Hello! Your question relates to previous discussions in this group.

Please take a moment to read the discussions below, as they may help answer your question.

{message_links}

You can also follow the conversations and wait for other group members or the admins to provide additional guidance.

⚠️ SECURITY NOTICE

Please beware of anyone contacting you privately while impersonating the group admin, Gabriel. I do not ask people to refer you to me through unsolicited DMs or collect payments through unofficial accounts. My only official Telegram username is @codewithgabby. Please verify any communication claiming to be from me.
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

    # Ignore updates that are not Business messages
    if not update.business_message:
        return {
            "ok": True,
            "message": "Update ignored",
        }

    business_message = update.business_message

    connection = await get_business_connection(
    business_message.business_connection_id
)

    business_user_id = connection["result"]["user"]["id"]

    # Ignore messages sent by the business account owner
    if business_message.from_.id == business_user_id:
        return {
            "ok": True,
            "message": "Business owner message ignored",
        }

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


@router.post("/group-telegram")
async def group_telegram_webhook(
    update: TelegramUpdate,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if x_telegram_bot_api_secret_token != GROUP_TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Invalid group webhook secret",
        )

    if not update.message:
        return {
            "ok": True,
            "message": "Update ignored",
        }

    return await handle_group_message(
        message=update.message,
        db=db,
    )


async def handle_group_message(
    message: GroupMessage,
    db: AsyncSession,
):
    # Ignore messages without text or a sender
    if not message.text or not message.from_:
        return {"ok": True, "message": "Message ignored"}

    # Ignore messages from bots
    if message.from_.is_bot:
        return {"ok": True, "message": "Bot message ignored"}

    # Check whether the sender is a group administrator
    member = await get_group_chat_member(
        chat_id=message.chat.id,
        user_id=message.from_.id,
    )

    status = member["result"]["status"]

    if status in ["creator", "administrator"]:
        return {
            "ok": True,
            "message": "Admin message ignored",
        }

    # Search for matching FAQ links
    matches = await find_matching_faqs(
        db=db,
        question=message.text,
    )

    if not matches:
        return {
            "ok": True,
            "message": "No matching FAQ found",
        }

    top_matches = []
    seen_links = set()

    for faq in matches:
        if faq.message_link not in seen_links:
            seen_links.add(faq.message_link)
            top_matches.append(faq)

        if len(top_matches) == 3:
            break

    links_text = "\n\n".join(
        f"{index}. {faq.topic}\n{faq.message_link}"
        for index, faq in enumerate(top_matches, start=1)
    )

    reply_text = GROUP_FAQ_REPLY.format(
        message_links=links_text,
    )

    await send_group_message(
        chat_id=message.chat.id,
        text=reply_text,
        reply_to_message_id=message.message_id,
    )

    return {
        "ok": True,
        "message": "FAQ reply sent",
        "topics": [faq.topic for faq in top_matches],
    }

    
