from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import StrategyBooking, StrategyCustomer


async def list_strategy_bookings(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 50,
    payment_status: str | None = None,
):
    query = select(StrategyBooking, StrategyCustomer).join(
        StrategyCustomer,
        StrategyBooking.customer_id == StrategyCustomer.id,
    )

    count_query = select(func.count(StrategyBooking.id))

    if payment_status:
        query = query.where(StrategyBooking.status == payment_status)
        count_query = count_query.where(StrategyBooking.status == payment_status)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = (
        query.order_by(StrategyBooking.created_at.desc()).offset(offset).limit(limit)
    )

    result = await db.execute(query)

    items = []

    for booking, customer in result.all():
        items.append(
            {
                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,
                "package_code": booking.package_code,
                "package_name": booking.package_name,
                "amount_ngn": booking.amount_ngn,
                "session_count": booking.session_count,
                "booking_status": booking.status,
                "created_at": booking.created_at,
                "customer": {
                    "id": customer.id,
                    "full_name": customer.full_name,
                    "email": customer.email,
                    "whatsapp": customer.whatsapp,
                    "country": customer.country,
                    "case_notes": customer.case_notes,
                },
            }
        )

    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }
