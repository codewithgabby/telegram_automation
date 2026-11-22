import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import StrategyService

INITIAL_SERVICES = [
    {
        "code": "single",
        "name": "Single Strategy Session",
        "description": "One strategy consultation session lasting 1 hour.",
        "price_ngn": 50000,
        "duration_minutes": 60,
        "session_count": 1,
        "features": [
            "One 1-hour strategy consultation",
            "Profile assessment and strategic guidance",
            "Opportunity to discuss your immigration concerns",
        ],
        "is_active": True,
        "display_order": 1,
    },
    {
        "code": "three",
        "name": "Three-Day Strategy",
        "description": "Three strategy consultation sessions, each lasting 1 hour.",
        "price_ngn": 100000,
        "duration_minutes": 60,
        "session_count": 3,
        "features": [
            "Three 1-hour strategy consultation sessions",
            "Profile assessment and strategic guidance",
            "Follow-up guidance across three sessions",
        ],
        "is_active": True,
        "display_order": 2,
    },
    {
        "code": "five",
        "name": "Five-Day Strategy",
        "description": "Five strategy consultation sessions, each lasting 1 hour.",
        "price_ngn": 150000,
        "duration_minutes": 60,
        "session_count": 5,
        "features": [
            "Five 1-hour strategy consultation sessions",
            "Profile assessment and strategic guidance",
            "Extended follow-up guidance across five sessions",
        ],
        "is_active": True,
        "display_order": 3,
    },
]


async def seed_services():
    async with AsyncSessionLocal() as db:
        created = 0
        skipped = 0

        for service_data in INITIAL_SERVICES:
            result = await db.execute(
                select(StrategyService).where(
                    StrategyService.code == service_data["code"]
                )
            )

            existing = result.scalar_one_or_none()

            if existing:
                print(
                    f"SKIPPED: {existing.code} already exists. "
                    "Existing settings preserved."
                )
                skipped += 1
                continue

            db.add(StrategyService(**service_data))
            created += 1

        await db.commit()

        print("\nSeeding completed.")
        print(f"Created: {created}")
        print(f"Skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(seed_services())
