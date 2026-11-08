from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    TelegramContact,
    ClientEngagementEvent,
)

# =========================================================
# SHARED HELPERS
# =========================================================


ANALYTICS_EVENT_TYPES = {
    "interested": "followup_interested",
    "paid": "payment_received",
    "completed": "session_completed",
    "replies": "client_replied",
}


def get_date_range(days: int = 30):
    """
    Return the start and end timestamps for an analytics period.
    The end timestamp is exclusive.
    """

    end_at = datetime.now(timezone.utc)
    start_at = end_at - timedelta(days=days)

    return start_at, end_at


async def count_distinct_event_contacts(
    db: AsyncSession,
    event_type: str,
    start_at: datetime,
    end_at: datetime,
) -> int:

    result = await db.execute(
        select(func.count(distinct(ClientEngagementEvent.contact_id))).where(
            ClientEngagementEvent.event_type == event_type,
            ClientEngagementEvent.occurred_at >= start_at,
            ClientEngagementEvent.occurred_at < end_at,
        )
    )

    return result.scalar_one() or 0


# =========================================================
# ANALYTICS SUMMARY
# =========================================================


async def get_analytics_summary(
    db: AsyncSession,
    start_at: datetime,
    end_at: datetime,
):
    # Contact timestamps use naive UTC in the existing database.
    contact_start_at = start_at.astimezone(timezone.utc).replace(tzinfo=None)
    contact_end_at = end_at.astimezone(timezone.utc).replace(tzinfo=None)

    # Period-based metrics
    enquiry_result = await db.execute(
        select(func.count(TelegramContact.id)).where(
            TelegramContact.first_seen_at >= contact_start_at,
            TelegramContact.first_seen_at < contact_end_at,
        )
    )
    enquiries = enquiry_result.scalar_one() or 0

    welcome_result = await db.execute(
        select(func.count(TelegramContact.id)).where(
            TelegramContact.welcome_status == "sent",
            TelegramContact.welcome_sent_at >= contact_start_at,
            TelegramContact.welcome_sent_at < contact_end_at,
        )
    )
    welcomes = welcome_result.scalar_one() or 0

    replies = await count_distinct_event_contacts(
        db, ANALYTICS_EVENT_TYPES["replies"], start_at, end_at
    )

    interested = await count_distinct_event_contacts(
        db, ANALYTICS_EVENT_TYPES["interested"], start_at, end_at
    )

    # Current business status: all contacts, regardless of reporting period.
    paid_result = await db.execute(
        select(func.count(TelegramContact.id)).where(
            TelegramContact.payment_status == "paid"
        )
    )
    paid = paid_result.scalar_one() or 0

    completed_result = await db.execute(
        select(func.count(TelegramContact.id)).where(
            TelegramContact.session_status == "completed"
        )
    )
    completed = completed_result.scalar_one() or 0

    return {
        "new_enquiries": enquiries,
        "welcome_delivered": welcomes,
        "client_replies": replies,
        "interested_leads": interested,
        "paid_clients": paid,
        "completed_sessions": completed,
        "period": {
            "start": start_at.isoformat(),
            "end": end_at.isoformat(),
        },
    }


# =========================================================
# ENQUIRY TRENDS
# =========================================================


async def get_enquiry_trends(
    db: AsyncSession,
    start_at: datetime,
    end_at: datetime,
):

    # Convert timezone-aware dates to naive UTC for contact timestamps.
    contact_start_at = start_at.astimezone(timezone.utc).replace(tzinfo=None)
    contact_end_at = end_at.astimezone(timezone.utc).replace(tzinfo=None)

    result = await db.execute(
        select(
            func.date(TelegramContact.first_seen_at).label("date"),
            func.count(TelegramContact.id).label("total"),
        )
        .where(
            TelegramContact.first_seen_at >= contact_start_at,
            TelegramContact.first_seen_at < contact_end_at,
        )
        .group_by(func.date(TelegramContact.first_seen_at))
        .order_by(func.date(TelegramContact.first_seen_at))
    )

    return [
        {
            "date": str(row.date),
            "total": row.total,
        }
        for row in result.all()
    ]


# =========================================================
# CONVERSION OVERVIEW
# =========================================================


async def get_conversion_overview(
    db: AsyncSession,
    start_at: datetime,
    end_at: datetime,
):
    summary = await get_analytics_summary(db, start_at, end_at)

    return {
        "enquiries": summary["new_enquiries"],
        "welcome_delivered": summary["welcome_delivered"],
        "client_replies": summary["client_replies"],
        "interested_leads": summary["interested_leads"],
        "paid_clients": summary["paid_clients"],
        "completed_sessions": summary["completed_sessions"],
    }


# =========================================================
# RECENT CLIENT ACTIVITY
# =========================================================


async def get_recent_activity(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
):
    total_result = await db.execute(select(func.count(ClientEngagementEvent.id)))

    total = total_result.scalar_one() or 0

    total_pages = (total + page_size - 1) // page_size

    result = await db.execute(
        select(
            ClientEngagementEvent,
            TelegramContact,
        )
        .join(
            TelegramContact,
            TelegramContact.id == ClientEngagementEvent.contact_id,
        )
        .order_by(
            ClientEngagementEvent.occurred_at.desc(),
            ClientEngagementEvent.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    rows = result.all()

    activities = [
        {
            "id": event.id,
            "contact_id": contact.id,
            "client_name": (
                f"{contact.first_name or ''} " f"{contact.last_name or ''}"
            ).strip()
            or contact.username
            or "Unknown client",
            "username": contact.username,
            "event_type": event.event_type,
            "description": event.description,
            "event_source": event.event_source,
            "occurred_at": event.occurred_at.isoformat(),
        }
        for event, contact in rows
    ]

    return {
        "activities": activities,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# =========================================================
# INDIVIDUAL CLIENT TIMELINE
# =========================================================


async def get_client_timeline(
    db: AsyncSession,
    contact_id: int,
):

    contact = await db.get(
        TelegramContact,
        contact_id,
    )

    if not contact:
        return None

    result = await db.execute(
        select(ClientEngagementEvent)
        .where(ClientEngagementEvent.contact_id == contact_id)
        .order_by(ClientEngagementEvent.occurred_at.desc())
    )

    events = result.scalars().all()

    return {
        "contact": {
            "id": contact.id,
            "username": contact.username,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "payment_status": contact.payment_status,
            "session_status": contact.session_status,
        },
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "previous_value": event.previous_value,
                "new_value": event.new_value,
                "description": event.description,
                "event_source": event.event_source,
                "occurred_at": event.occurred_at.isoformat(),
            }
            for event in events
        ],
    }
