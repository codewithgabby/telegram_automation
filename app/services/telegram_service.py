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