import os
import asyncio
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine

from app.routers.telegram import router as telegram_router
from app.routers.faq import router as faq_router
from app.routers.auth import router as auth_router
from app.routers.contacts import router as contacts_router

from app.services.follow_up_service import scheduler_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_task = asyncio.create_task(scheduler_loop())

    logger.info("FastAPI application started")
    logger.info("Client follow-up scheduler started")

    try:
        yield

    finally:
        scheduler_task.cancel()

        try:
            await scheduler_task
        except asyncio.CancelledError:
            logger.info("Follow-up scheduler stopped")

        await engine.dispose()

        logger.info("Database connections disposed")
        logger.info("FastAPI application stopped")


app = FastAPI(
    title="Telegram Auto Reply",
    description="Telegram Business automation and Pathway to Canada FAQ assistant",
    version="1.3.0",
    lifespan=lifespan,
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
app.include_router(contacts_router)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Telegram Auto Reply API is running",
    }
