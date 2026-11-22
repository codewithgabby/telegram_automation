from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    AdminUser,
    StrategyService,
    StrategyContentSection,
)
from app.routers.auth import get_current_admin
from app.schemas.strategy_content import (
    StrategyServiceCreate,
    StrategyServiceUpdate,
    StrategyServiceResponse,
    StrategySettingUpsert,
    StrategySettingResponse,
    StrategyContentCreate,
    StrategyContentUpdate,
    StrategyContentResponse,
    StrategyPublicContentResponse,
)
from app.services import strategy_content_service as service
from app.services.strategy_admin_payment_service import (
    list_strategy_bookings,
)

router = APIRouter(
    prefix="/api/strategy",
    tags=["Strategy Session Content"],
)

admin_router = APIRouter(
    prefix="/admin/strategy",
    tags=["Admin - Strategy Session"],
)


# ============================================================
# PUBLIC STRATEGY SESSION CONTENT
# ============================================================


@router.get(
    "/site",
    response_model=StrategyPublicContentResponse,
)
async def public_site_content(
    db: AsyncSession = Depends(get_db),
):
    return await service.get_public_strategy_content(db)


# ============================================================
# ADMIN: PACKAGE MANAGEMENT
# ============================================================


@admin_router.get(
    "/services",
    response_model=list[StrategyServiceResponse],
)
async def admin_list_services(
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await service.list_services(db)


@admin_router.post(
    "/services",
    response_model=StrategyServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_service(
    data: StrategyServiceCreate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    try:
        return await service.create_service(
            db,
            data.model_dump(),
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            409,
            "A package with this code already exists.",
        )


@admin_router.patch(
    "/services/{service_id}",
    response_model=StrategyServiceResponse,
)
async def admin_update_service(
    service_id: int,
    data: StrategyServiceUpdate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    item = await db.get(StrategyService, service_id)

    if not item:
        raise HTTPException(
            404,
            "Package not found.",
        )

    return await service.update_service(
        db,
        item,
        data.model_dump(exclude_unset=True),
    )


# ============================================================
# ADMIN: WEBSITE SETTINGS
# ============================================================


@admin_router.get(
    "/settings",
    response_model=list[StrategySettingResponse],
)
async def admin_list_settings(
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await service.list_settings(db)


@admin_router.put(
    "/settings/{key}",
    response_model=StrategySettingResponse,
)
async def admin_upsert_setting(
    key: str,
    data: StrategySettingUpsert,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await service.upsert_setting(
        db,
        key,
        data.value,
        data.is_public,
    )


# ============================================================
# ADMIN: WEBSITE CONTENT SECTIONS
# ============================================================


@admin_router.get(
    "/sections",
    response_model=list[StrategyContentResponse],
)
async def admin_list_sections(
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await service.list_content_sections(db)


@admin_router.post(
    "/sections",
    response_model=StrategyContentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_section(
    data: StrategyContentCreate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    try:
        return await service.create_content_section(
            db,
            data.model_dump(),
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            409,
            "This section key already exists.",
        )


@admin_router.patch(
    "/sections/{section_id}",
    response_model=StrategyContentResponse,
)
async def admin_update_section(
    section_id: int,
    data: StrategyContentUpdate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    item = await db.get(
        StrategyContentSection,
        section_id,
    )

    if not item:
        raise HTTPException(
            404,
            "Content section not found.",
        )

    return await service.update_content_section(
        db,
        item,
        data.model_dump(exclude_unset=True),
    )


# ============================================================
# ADMIN: STRATEGY SESSION BOOKINGS
# ============================================================


@admin_router.get("/bookings")
async def admin_list_strategy_bookings(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    payment_status: str | None = Query(default=None, max_length=30),
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await list_strategy_bookings(
        db=db,
        offset=offset,
        limit=limit,
        payment_status=payment_status,
    )
