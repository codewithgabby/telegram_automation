from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClientEngagementEvent


async def record_engagement_event(
    db: AsyncSession,
    contact_id: int,
    event_type: str,
    event_source: str,
    description: str | None = None,
    previous_value: str | None = None,
    new_value: str | None = None,
    metadata: dict | None = None,
) -> ClientEngagementEvent:
    """
    Add an engagement event to the current database transaction.

    This function deliberately does not commit.
    The calling service controls the transaction.
    """

    event = ClientEngagementEvent(
        contact_id=contact_id,
        event_type=event_type,
        event_source=event_source,
        description=description,
        previous_value=previous_value,
        new_value=new_value,
        metadata_json=metadata,
        occurred_at=datetime.now(timezone.utc),
    )

    db.add(event)

    await db.flush()

    return event
