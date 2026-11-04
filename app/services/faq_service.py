import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GroupFAQLink


async def create_faq(
    db: AsyncSession,
    faq_data: dict,
) -> GroupFAQLink:
    faq = GroupFAQLink(
        topic=faq_data["topic"],
        keywords=faq_data["keywords"],
        message_link=str(faq_data["message_link"]),
    )

    db.add(faq)
    await db.commit()
    await db.refresh(faq)

    return faq


async def get_faq_by_id(
    db: AsyncSession,
    faq_id: int,
) -> GroupFAQLink | None:
    result = await db.execute(select(GroupFAQLink).where(GroupFAQLink.id == faq_id))

    return result.scalar_one_or_none()


async def get_all_faqs(
    db: AsyncSession,
) -> list[GroupFAQLink]:
    result = await db.execute(
        select(GroupFAQLink).order_by(GroupFAQLink.created_at.desc())
    )

    return list(result.scalars().all())


async def update_faq(
    db: AsyncSession,
    faq: GroupFAQLink,
    update_data: dict,
) -> GroupFAQLink:
    for field, value in update_data.items():
        if field == "message_link":
            value = str(value)

        setattr(faq, field, value)

    await db.commit()
    await db.refresh(faq)

    return faq


async def deactivate_faq(
    db: AsyncSession,
    faq: GroupFAQLink,
) -> GroupFAQLink:
    faq.is_active = False

    await db.commit()
    await db.refresh(faq)

    return faq


async def delete_faq(
    db: AsyncSession,
    faq: GroupFAQLink,
) -> None:
    await db.delete(faq)
    await db.commit()


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
        matched_keywords = []

        for keyword in faq.keywords:
            pattern = rf"(?<!\w){re.escape(keyword.lower())}(?!\w)"

            if re.search(pattern, question_text):
                matched_keywords.append(keyword)

        if matched_keywords:
            matches.append((faq, len(matched_keywords)))

    matches.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return [faq for faq, score in matches]
