# Telegram Auto Reply

A simple FastAPI service that automatically responds to new messages received through a Telegram Business account.

## Features

- Telegram Business message webhook
- New contact detection
- PostgreSQL contact storage
- Automatic welcome message
- Duplicate-contact prevention
- Secure webhook verification

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Telegram Bot API
- HTTPX

## Environment Variables

The application requires:

- `DATABASE_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`

See `.env.example` for the required format.

## Local Development

Install dependencies:

```bash
pip install -r requirements.txt