import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.telegram import router as telegram_router
from app.routers.faq import router as faq_router
from app.routers.auth import router as auth_router

app = FastAPI(
    title="Telegram Auto Reply",
    description="Telegram Business automation and Pathway to Canada FAQ assistant",
    version="1.2.0",
)

frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5500,http://127.0.0.1:5500",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in frontend_origins],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(telegram_router)
app.include_router(faq_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Telegram Auto Reply API is running",
    }
