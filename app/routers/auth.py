from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AdminUser
from app.services.auth_service import (
    authenticate_admin,
    create_admin_session,
    get_admin_session,
    delete_admin_session,
)

router = APIRouter(
    prefix="/admin/auth",
    tags=["Admin Authentication"],
)

SESSION_DURATION_HOURS = 12

bearer_scheme = HTTPBearer(auto_error=False)


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1)


class AdminLoginResponse(BaseModel):
    message: str
    username: str
    access_token: str
    token_type: str
    expires_in: int


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    session_token = credentials.credentials

    session = await get_admin_session(
        db=db,
        session_token=session_token,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid or expired",
        )

    admin = await db.get(AdminUser, session.admin_user_id)

    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator account is inactive",
        )

    return admin


@router.post(
    "/login",
    response_model=AdminLoginResponse,
)
async def admin_login(
    login_data: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
):

    admin = await authenticate_admin(
        db=db,
        username=login_data.username,
        password=login_data.password,
    )

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    session_token, _ = await create_admin_session(
        db=db,
        admin_user_id=admin.id,
    )

    return {
        "message": "Login successful",
        "username": admin.username,
        "access_token": session_token,
        "token_type": "Bearer",
        "expires_in": SESSION_DURATION_HOURS * 60 * 60,
    }


@router.get("/me")
async def get_logged_in_admin(
    admin: AdminUser = Depends(get_current_admin),
):
    return {
        "authenticated": True,
        "username": admin.username,
    }


@router.post("/logout")
async def admin_logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):

    session = await get_admin_session(
        db=db,
        session_token=credentials.credentials,
    )

    if session:
        await delete_admin_session(db, session)

    return {
        "message": "Logout successful",
    }
