from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.faq import FAQCreate, FAQUpdate, FAQResponse
from app.routers.auth import get_current_admin
from app.services.faq_service import (
    create_faq,
    get_faq_by_id,
    get_all_faqs,
    update_faq,
    deactivate_faq,
    delete_faq,
)

router = APIRouter(
    prefix="/admin/faqs",
    tags=["FAQ Management"],
    dependencies=[Depends(get_current_admin)],
)


@router.post(
    "",
    response_model=FAQResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_faq_endpoint(
    faq_data: FAQCreate,
    db: AsyncSession = Depends(get_db),
):
    return await create_faq(
        db=db,
        faq_data=faq_data.model_dump(),
    )


@router.get(
    "",
    response_model=list[FAQResponse],
)
async def get_all_faqs_endpoint(
    db: AsyncSession = Depends(get_db),
):
    return await get_all_faqs(db)


@router.get(
    "/{faq_id}",
    response_model=FAQResponse,
)
async def get_faq_endpoint(
    faq_id: int,
    db: AsyncSession = Depends(get_db),
):
    faq = await get_faq_by_id(db, faq_id)

    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found",
        )

    return faq


@router.patch(
    "/{faq_id}",
    response_model=FAQResponse,

)
async def update_faq_endpoint(
    faq_id: int,
    update_data: FAQUpdate,
    db: AsyncSession = Depends(get_db),
):
    faq = await get_faq_by_id(db, faq_id)

    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found",
        )

    changes = update_data.model_dump(exclude_unset=True)

    return await update_faq(
        db=db,
        faq=faq,
        update_data=changes,
    )


@router.patch(
    "/{faq_id}/deactivate",
    response_model=FAQResponse,

)
async def deactivate_faq_endpoint(
    faq_id: int,
    db: AsyncSession = Depends(get_db),
):
    faq = await get_faq_by_id(db, faq_id)

    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found",
        )

    return await deactivate_faq(db, faq)


@router.delete(
    "/{faq_id}",
    status_code=status.HTTP_204_NO_CONTENT,

)
async def delete_faq_endpoint(
    faq_id: int,
    db: AsyncSession = Depends(get_db),
):
    faq = await get_faq_by_id(db, faq_id)

    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found",
        )

    await delete_faq(db, faq)

    return None
