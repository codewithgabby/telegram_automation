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
from app.routers.analytics import router as analytics_router
from app.routers.strategy_bookings import router as strategy_bookings_router
from app.routers import strategy_content



from app.routers.strategy_customer_telegram import (
    router as strategy_customer_telegram_router,
)

from app.services.follow_up_service import scheduler_loop

from app.services.strategy_admin_notification_service import (
    strategy_admin_notification_scheduler_loop,
)

from app.services.strategy_customer_notification_service import (
    strategy_customer_notification_scheduler_loop,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_task = asyncio.create_task(scheduler_loop())

    strategy_notification_task = asyncio.create_task(
        strategy_admin_notification_scheduler_loop()
    )

    customer_notification_task = asyncio.create_task(
        strategy_customer_notification_scheduler_loop()
    )

    logger.info("FastAPI application started")
    logger.info("Client follow-up scheduler started")
    logger.info("Strategy administrator notification scheduler started")
    logger.info("Strategy customer notification scheduler started")

    try:
        yield

    finally:
        scheduler_task.cancel()
        strategy_notification_task.cancel()
        customer_notification_task.cancel()

        for task, task_name in (
            (scheduler_task, "Follow-up scheduler"),
            (
                strategy_notification_task,
                "Strategy administrator notification scheduler",
            ),
            (
                customer_notification_task,
                "Strategy customer notification scheduler",
            ),
        ):
            try:
                await task
            except asyncio.CancelledError:
                logger.info("%s stopped", task_name)

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

allowed_origins = [origin.strip() for origin in frontend_origins if origin.strip()]

for origin in (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
):
    if origin not in allowed_origins:
        allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=["Content-Type", "Authorization"],
)


app.include_router(telegram_router)
app.include_router(faq_router)
app.include_router(auth_router)
app.include_router(contacts_router)
app.include_router(analytics_router)
app.include_router(strategy_bookings_router)
app.include_router(strategy_content.router)
app.include_router(strategy_content.admin_router)
app.include_router(strategy_customer_telegram_router)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Telegram Auto Reply API is running",
    }
