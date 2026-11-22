from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    StrategyService,
    StrategySiteSetting,
    StrategyContentSection,
)


async def get_public_strategy_content(db: AsyncSession):
    services_result = await db.execute(
        select(StrategyService)
        .where(StrategyService.is_active.is_(True))
        .order_by(StrategyService.display_order, StrategyService.id)
    )

    sections_result = await db.execute(
        select(StrategyContentSection)
        .where(StrategyContentSection.is_active.is_(True))
        .order_by(
            StrategyContentSection.display_order,
            StrategyContentSection.id,
        )
    )

    settings_result = await db.execute(
        select(StrategySiteSetting).where(StrategySiteSetting.is_public.is_(True))
    )

    return {
        "services": services_result.scalars().all(),
        "sections": sections_result.scalars().all(),
        "settings": {item.key: item.value for item in settings_result.scalars().all()},
    }


async def list_services(db: AsyncSession):
    result = await db.execute(
        select(StrategyService).order_by(
            StrategyService.display_order,
            StrategyService.id,
        )
    )
    return result.scalars().all()


async def create_service(db: AsyncSession, data: dict):
    service = StrategyService(**data)
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


async def update_service(
    db: AsyncSession,
    service: StrategyService,
    data: dict,
):
    for key, value in data.items():
        if value is not None:
            setattr(service, key, value)

    await db.commit()
    await db.refresh(service)
    return service


async def list_settings(db: AsyncSession):
    result = await db.execute(
        select(StrategySiteSetting).order_by(StrategySiteSetting.key)
    )
    return result.scalars().all()


async def upsert_setting(
    db: AsyncSession,
    key: str,
    value: dict,
    is_public: bool,
):
    result = await db.execute(
        select(StrategySiteSetting).where(StrategySiteSetting.key == key)
    )
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = value
        setting.is_public = is_public
    else:
        setting = StrategySiteSetting(
            key=key,
            value=value,
            is_public=is_public,
        )
        db.add(setting)

    await db.commit()
    await db.refresh(setting)
    return setting


async def list_content_sections(db: AsyncSession):
    result = await db.execute(
        select(StrategyContentSection).order_by(
            StrategyContentSection.display_order,
            StrategyContentSection.id,
        )
    )
    return result.scalars().all()


async def create_content_section(db: AsyncSession, data: dict):
    section = StrategyContentSection(**data)
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section


async def update_content_section(
    db: AsyncSession,
    section: StrategyContentSection,
    data: dict,
):
    for key, value in data.items():
        if value is not None:
            setattr(section, key, value)

    await db.commit()
    await db.refresh(section)
    return section
