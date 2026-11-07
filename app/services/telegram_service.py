import os

import httpx
from dotenv import load_dotenv

load_dotenv()


def get_business_telegram_api_url():
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

    return f"https://api.telegram.org/bot{token}"


async def send_business_message(
    business_connection_id: str,
    chat_id: int,
    text: str,
    reply_markup: dict | None = None,
) -> dict:
    api_url = get_business_telegram_api_url()

    payload = {
        "business_connection_id": business_connection_id,
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{api_url}/sendMessage",
            json=payload,
        )

    response.raise_for_status()
    return response.json()


async def get_business_connection(
    business_connection_id: str,
) -> dict:
    api_url = get_business_telegram_api_url()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{api_url}/getBusinessConnection",
            params={
                "business_connection_id": business_connection_id,
            },
        )

    response.raise_for_status()
    return response.json()


async def answer_callback_query(
    callback_query_id: str,
    text: str | None = None,
) -> dict:
    api_url = get_business_telegram_api_url()

    payload = {
        "callback_query_id": callback_query_id,
    }

    if text:
        payload["text"] = text

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{api_url}/answerCallbackQuery",
            json=payload,
        )

    response.raise_for_status()
    return response.json()
