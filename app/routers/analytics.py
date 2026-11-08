from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import get_current_admin

from app.services.analytics_service import (
    get_analytics_summary,
    get_enquiry_trends,
    get_conversion_overview,
    get_recent_activity,
    get_client_timeline,
)

router = APIRouter(
    prefix="/admin/analytics",
    tags=["Client Engagement Analytics"],
    dependencies=[Depends(get_current_admin)],
)


# =========================================================
# DATE RANGE HELPER
# =========================================================


def resolve_date_range(
    days: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):

    if (start_date is None) != (end_date is None):
        raise HTTPException(
            status_code=400,
            detail="Both start_date and end_date are required.",
        )

    if start_date and end_date:

        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)

        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        if start_date >= end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be earlier than end_date.",
            )

        return start_date, end_date

    end_at = datetime.now(timezone.utc)
    start_at = end_at - timedelta(days=days)

    return start_at, end_at


# =========================================================
# ANALYTICS SUMMARY
# =========================================================


@router.get("/summary")
async def analytics_summary(
    days: int = Query(default=30, ge=1, le=365),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):

    start_at, end_at = resolve_date_range(
        days,
        start_date,
        end_date,
    )

    return await get_analytics_summary(
        db,
        start_at,
        end_at,
    )


# =========================================================
# ENQUIRY TRENDS
# =========================================================


@router.get("/trends")
async def analytics_trends(
    days: int = Query(default=30, ge=1, le=365),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):

    start_at, end_at = resolve_date_range(
        days,
        start_date,
        end_date,
    )

    return {
        "trends": await get_enquiry_trends(
            db,
            start_at,
            end_at,
        ),
        "start_date": start_at.isoformat(),
        "end_date": end_at.isoformat(),
    }


# =========================================================
# CONVERSION OVERVIEW
# =========================================================


@router.get("/conversions")
async def analytics_conversions(
    days: int = Query(default=30, ge=1, le=365),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):

    start_at, end_at = resolve_date_range(
        days,
        start_date,
        end_date,
    )

    return await get_conversion_overview(
        db,
        start_at,
        end_at,
    )


# =========================================================
# RECENT ACTIVITY
# =========================================================


@router.get("/activity")
async def analytics_activity(
    page: int = Query(default=1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    return await get_recent_activity(
        db,
        page=page,
        page_size=10,
    )


# =========================================================
# INDIVIDUAL CLIENT TIMELINE
# =========================================================


@router.get("/clients/{contact_id}/timeline")
async def analytics_client_timeline(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
):

    timeline = await get_client_timeline(
        db,
        contact_id,
    )

    if timeline is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found.",
        )

    return timeline
