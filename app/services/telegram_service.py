import os

import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

TELEGRAM_API_URL = (
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
)


async def send_business_message(
    business_connection_id: str,
    chat_id: int,
    text: str,
) -> dict:

    payload = {
        "business_connection_id": business_connection_id,
        "chat_id": chat_id,
        "text": text,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json=payload,
        )

    response.raise_for_status()

    return response.json()


async def send_group_message(
    chat_id: int,
    text: str,
    reply_to_message_id: int,
) -> dict:

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_to_message_id": reply_to_message_id,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json=payload,
        )

    response.raise_for_status()

    return response.json()


async def get_business_connection(
    business_connection_id: str,
) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TELEGRAM_API_URL}/getBusinessConnection",
            params={
                "business_connection_id": business_connection_id,
            },
        )

    response.raise_for_status()

    return response.json()


async def get_chat_member(
    chat_id: int,
    user_id: int,
) -> dict:

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TELEGRAM_API_URL}/getChatMember",
            params={
                "chat_id": chat_id,
                "user_id": user_id,
            },
        )

    response.raise_for_status()

    return response.json()
