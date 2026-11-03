from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GroupFAQLink


async def get_active_faq_links(
    db: AsyncSession,
) -> list[GroupFAQLink]:
    result = await db.execute(
        select(GroupFAQLink).where(GroupFAQLink.is_active.is_(True))
    )

    return list(result.scalars().all())


async def find_matching_faqs(
    db: AsyncSession,
    question: str,
) -> list[GroupFAQLink]:
    faq_links = await get_active_faq_links(db)

    question_text = question.lower()

    matches = []

    for faq in faq_links:
        matched_keywords = [
            keyword for keyword in faq.keywords if keyword.lower() in question_text
        ]

        if matched_keywords:
            matches.append((faq, len(matched_keywords)))

    matches.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return [faq for faq, score in matches]
