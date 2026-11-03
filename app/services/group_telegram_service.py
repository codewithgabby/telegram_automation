import os

import httpx
from dotenv import load_dotenv

load_dotenv()


def get_group_telegram_api_url():
    token = os.getenv("GROUP_TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError("GROUP_TELEGRAM_BOT_TOKEN is missing")

    return f"https://api.telegram.org/bot{token}"


async def send_group_message(
    chat_id: int,
    text: str,
    reply_to_message_id: int,
) -> dict:

    api_url = get_group_telegram_api_url()

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_to_message_id": reply_to_message_id,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{api_url}/sendMessage",
            json=payload,
        )

    response.raise_for_status()

    return response.json()


async def get_group_chat_member(
    chat_id: int,
    user_id: int,
) -> dict:

    api_url = get_group_telegram_api_url()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{api_url}/getChatMember",
            params={
                "chat_id": chat_id,
                "user_id": user_id,
            },
        )

    response.raise_for_status()

    return response.json()
