from fastapi import FastAPI

from app.routers.telegram import router as telegram_router

app = FastAPI(
    title="Telegram Auto Reply",
    description="Simple Telegram Business auto-reply service",
    version="1.0.0",
)

app.include_router(telegram_router)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Telegram Auto Reply API is running",
    }