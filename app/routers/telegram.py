import os
import logging
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ClientFollowUp
from app.schemas.telegram import TelegramUpdate, GroupMessage

from app.services.contact_service import (
    create_contact,
    get_contact,
    record_incoming_message,
    begin_welcome_delivery,
    complete_welcome_delivery,
    fail_welcome_delivery,
)

from app.services.telegram_service import (
    get_business_connection,
    send_business_message,
    answer_callback_query,
)

from app.services.group_telegram_service import (
    get_group_chat_member,
    send_group_message,
)

from app.services.faq_service import find_matching_faqs

from app.services.webhook_event_service import (
    claim_webhook_event,
    complete_webhook_event,
    fail_webhook_event,
)

load_dotenv()

logger = logging.getLogger(__name__)

TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")
GROUP_TELEGRAM_WEBHOOK_SECRET = os.getenv("GROUP_TELEGRAM_WEBHOOK_SECRET")

router = APIRouter(prefix="/webhook", tags=["Telegram"])


WELCOME_MESSAGE = """Hello Sir/Ma'am, welcome.

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


BOOKING_LINK_MESSAGE = """Thank you for your interest!

You can explore and book your Personalized Strategy Session here:

https://strategysession.netlify.app/

You'll be able to choose the session that best fits your situation."""


# =========================================================
# BUSINESS WEBHOOK
# =========================================================


@router.post("/telegram")
async def telegram_webhook(
    update: TelegramUpdate,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if (
        not TELEGRAM_WEBHOOK_SECRET
        or x_telegram_bot_api_secret_token != TELEGRAM_WEBHOOK_SECRET
    ):
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    claimed = await claim_webhook_event(
        db=db,
        update_id=update.update_id,
        webhook_type="business",
    )

    if not claimed:
        return {
            "ok": True,
            "message": "Duplicate Business update ignored",
        }

    try:
        result = await process_business_update(update, db)

        await complete_webhook_event(
            db=db,
            update_id=update.update_id,
            webhook_type="business",
        )

        return result

    except Exception as exc:
        await db.rollback()

        try:
            await fail_webhook_event(
                db=db,
                update_id=update.update_id,
                webhook_type="business",
                error=str(exc),
            )
        except Exception:
            logger.exception("Could not record failed Business update")

        logger.exception(
            "Business webhook update %s failed",
            update.update_id,
        )

        raise HTTPException(
            status_code=503,
            detail="Business update processing failed",
        ) from exc


async def process_business_update(
    update: TelegramUpdate,
    db: AsyncSession,
):
    if update.callback_query:
        return await handle_business_callback(update, db)

    if not update.business_message:
        return {"ok": True, "message": "Update ignored"}

    message = update.business_message

    try:
        connection = await get_business_connection(message.business_connection_id)
        business_user_id = connection["result"]["user"]["id"]

    except Exception as exc:
        logger.exception("Could not verify Telegram Business connection")
        raise RuntimeError("Business connection unavailable") from exc

    if message.from_.id == business_user_id:
        return {"ok": True, "message": "Business owner message ignored"}

    contact = await get_contact(db, message.from_.id)

    if not contact:
        contact = await create_contact(
            db=db,
            telegram_user_id=message.from_.id,
            chat_id=message.chat.id,
            username=message.from_.username,
            first_name=message.from_.first_name,
            last_name=message.from_.last_name,
            business_connection_id=message.business_connection_id,
        )

    # Keep the latest Telegram contact information.
    contact.chat_id = message.chat.id
    contact.business_connection_id = message.business_connection_id
    contact.username = message.from_.username
    contact.first_name = message.from_.first_name
    contact.last_name = message.from_.last_name

    # Attempt welcome delivery only when the contact is pending.
    if contact.welcome_status == "pending":
        reserved = await begin_welcome_delivery(
            db=db,
            contact=contact,
            business_connection_id=message.business_connection_id,
        )

        if not reserved:
            return {
                "ok": True,
                "message": "Welcome delivery was already attempted or reserved",
                "contact_id": contact.id,
            }

        try:
            await send_business_message(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                text=WELCOME_MESSAGE,
            )

            await complete_welcome_delivery(
                db=db,
                contact=contact,
            )

            return {
                "ok": True,
                "message": "Welcome message successfully sent and recorded",
                "contact_id": contact.id,
            }

        except Exception as exc:
            await db.rollback()

            try:
                await fail_welcome_delivery(
                    db=db,
                    contact=contact,
                    error=str(exc),
                )
            except Exception:
                await db.rollback()
                logger.exception(
                    "Could not record failed welcome delivery for contact %s",
                    contact.id,
                )

            logger.exception(
                "Welcome delivery failed or could not be confirmed for contact %s",
                contact.id,
            )

            raise RuntimeError(
                "Welcome delivery failed or could not be confirmed"
            ) from exc

    # Existing contacts who have already received their welcome
    # have now sent another message. Record their reply and cancel
    # any pending follow-up.
    if contact.welcome_status == "sent":
        await record_incoming_message(
            db=db,
            contact=contact,
        )

        return {
            "ok": True,
            "message": "Existing contact reply recorded",
            "contact_id": contact.id,
        }

    # Sending or failed contacts must not receive an automatic
    # duplicate welcome message. However, record their new activity.
    logger.warning(
        "Welcome delivery requires review for contact %s. Status: %s",
        contact.id,
         contact.welcome_status,
    )

    await record_incoming_message(
        db=db,
        contact=contact,
    )

    return {
        "ok": True,
        "message": "Incoming activity recorded; welcome delivery requires review",
        "contact_id": contact.id,
    }


# =========================================================
# BUSINESS FOLLOW-UP BUTTON CALLBACKS
# =========================================================


async def handle_business_callback(
    update: TelegramUpdate,
    db: AsyncSession,
):
    callback = update.callback_query

    if not callback:
        return {"ok": True, "message": "Callback ignored"}

    if callback.data not in (
        "followup_interested",
        "followup_not_now",
    ):
        await answer_callback_query(
            callback_query_id=callback.id,
            text="This action is not recognised.",
        )
        return {"ok": True, "message": "Unknown callback"}

    contact = await get_contact(db, callback.from_.id)

    if not contact:
        await answer_callback_query(
            callback_query_id=callback.id,
            text="We couldn't find your conversation.",
        )
        return {"ok": True, "message": "Contact not found"}

    callback_business_connection_id = (
        callback.message.business_connection_id if callback.message else None
    )

    if (
        not callback_business_connection_id
        or callback_business_connection_id != contact.business_connection_id
    ):
        await answer_callback_query(
            callback_query_id=callback.id,
            text="This conversation could not be verified.",
        )
        return {
            "ok": True,
            "message": "Business connection validation failed",
        }

    result = await db.execute(
        select(ClientFollowUp)
        .where(
            ClientFollowUp.contact_id == contact.id,
            ClientFollowUp.status == "sent",
        )
        .with_for_update()
    )

    follow_up = result.scalar_one_or_none()

    if not follow_up:
        await answer_callback_query(
            callback_query_id=callback.id,
            text="This follow-up is no longer active.",
        )
        return {"ok": True, "message": "No active follow-up"}

    if follow_up.response is not None:
        await answer_callback_query(
            callback_query_id=callback.id,
            text="We've already recorded your response. Thank you!",
        )
        return {"ok": True, "message": "Response already recorded"}

    if callback.data == "followup_not_now":
        follow_up.response = "not_now"
        await db.commit()

        await answer_callback_query(
            callback_query_id=callback.id,
            text="No problem. Thank you for letting us know!",
        )

        return {"ok": True, "message": "Not now response recorded"}

    follow_up.response = "interested"
    await db.commit()

    await answer_callback_query(
        callback_query_id=callback.id,
        text="Thank you! Here's how to book your session.",
    )

    if not contact.welcome_sent_at or not contact.business_connection_id:
        return {
            "ok": True,
            "message": "Interest recorded; Business details unavailable",
        }

    welcome_sent_at = contact.welcome_sent_at

    if welcome_sent_at.tzinfo is None:
        welcome_sent_at = welcome_sent_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) - welcome_sent_at >= timedelta(hours=24):
        return {
            "ok": True,
            "message": "Interest recorded; Telegram reply window expired",
        }

    try:
        connection = await get_business_connection(contact.business_connection_id)

        details = connection.get("result", {})
        rights = details.get("rights") or {}

        if not details.get("is_enabled") or not rights.get("can_reply"):
            return {
                "ok": True,
                "message": "Interest recorded; messaging permission unavailable",
            }

        await send_business_message(
            business_connection_id=contact.business_connection_id,
            chat_id=contact.chat_id,
            text=BOOKING_LINK_MESSAGE,
        )

    except Exception:
        logger.exception(
            "Could not send booking link to contact %s",
            contact.id,
        )

    return {"ok": True, "message": "Interest recorded"}


# =========================================================
# GROUP WEBHOOK
# =========================================================


@router.post("/group-telegram")
async def group_telegram_webhook(
    update: TelegramUpdate,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if (
        not GROUP_TELEGRAM_WEBHOOK_SECRET
        or x_telegram_bot_api_secret_token != GROUP_TELEGRAM_WEBHOOK_SECRET
    ):
        raise HTTPException(status_code=403, detail="Invalid group webhook secret")

    claimed = await claim_webhook_event(
        db=db,
        update_id=update.update_id,
        webhook_type="group",
    )

    if not claimed:
        return {
            "ok": True,
            "message": "Duplicate Group update ignored",
        }

    try:
        if update.message:
            result = await handle_group_message(update.message, db)
        else:
            result = {"ok": True, "message": "Update ignored"}

        await complete_webhook_event(
            db=db,
            update_id=update.update_id,
            webhook_type="group",
        )

        return result

    except Exception as exc:
        await db.rollback()

        try:
            await fail_webhook_event(
                db=db,
                update_id=update.update_id,
                webhook_type="group",
                error=str(exc),
            )
        except Exception:
            logger.exception("Could not record failed Group update")

        logger.exception(
            "Group webhook update %s failed",
            update.update_id,
        )

        raise HTTPException(
            status_code=503,
            detail="Group update processing failed",
        ) from exc


# =========================================================
# EXISTING GROUP FAQ HANDLER — PRESERVED
# =========================================================


async def handle_group_message(
    message: GroupMessage,
    db: AsyncSession,
):
    if not message.text or not message.from_:
        return {"ok": True, "message": "Message ignored"}

    if message.from_.is_bot:
        return {"ok": True, "message": "Bot message ignored"}

    member = await get_group_chat_member(
        chat_id=message.chat.id,
        user_id=message.from_.id,
    )

    status = member["result"]["status"]

    if status in ["creator", "administrator"]:
        return {"ok": True, "message": "Admin message ignored"}

    matches = await find_matching_faqs(
        db=db,
        question=message.text,
    )

    if not matches:
        return {"ok": True, "message": "No matching FAQ found"}

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
