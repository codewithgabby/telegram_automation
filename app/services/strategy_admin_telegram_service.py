import os
import logging

import httpx

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_admin_telegram_configuration() -> tuple[str, int]:
    token = os.getenv("STRATEGY_ADMIN_TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("STRATEGY_ADMIN_TELEGRAM_CHAT_ID")

    if not token:
        raise RuntimeError("STRATEGY_ADMIN_TELEGRAM_BOT_TOKEN is missing.")

    if not chat_id:
        raise RuntimeError("STRATEGY_ADMIN_TELEGRAM_CHAT_ID is missing.")

    try:
        parsed_chat_id = int(chat_id)
    except ValueError as exc:
        raise RuntimeError(
            "STRATEGY_ADMIN_TELEGRAM_CHAT_ID must be an integer."
        ) from exc

    return token, parsed_chat_id


async def send_strategy_admin_message(
    message: str,
) -> dict:
    token, chat_id = get_admin_telegram_configuration()

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": True,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            api_url,
            json=payload,
        )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError("Telegram did not confirm administrator message delivery.")

    return result
