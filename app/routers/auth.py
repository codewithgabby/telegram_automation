import os
import secrets
from datetime import timedelta

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
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

SESSION_COOKIE_NAME = "admin_session"
CSRF_COOKIE_NAME = "admin_csrf"

SESSION_DURATION_HOURS = 12


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1)


class AdminLoginResponse(BaseModel):
    message: str
    username: str
    csrf_token: str


async def get_current_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    session_token = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

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


async def verify_csrf(
    request: Request,
    x_csrf_token: str | None = Header(default=None),
):
    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)

    if (
        not csrf_cookie
        or not x_csrf_token
        or not secrets.compare_digest(
            csrf_cookie,
            x_csrf_token,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        )


@router.post(
    "/login",
    response_model=AdminLoginResponse,
)
async def admin_login(
    login_data: AdminLoginRequest,
    response: Response,
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

    session_token, session = await create_admin_session(
        db=db,
        admin_user_id=admin.id,
    )

    csrf_token = secrets.token_urlsafe(32)

    is_production = os.getenv("APP_ENV", "development").lower() == "production"

    cookie_samesite = "none" if is_production else "lax"

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_DURATION_HOURS * 60 * 60,
        httponly=True,
        secure=is_production,
        samesite=cookie_samesite,
        path="/",
    )

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=SESSION_DURATION_HOURS * 60 * 60,
        httponly=False,
        secure=is_production,
        samesite=cookie_samesite,
        path="/",
    )

    return {
        "message": "Login successful",
        "username": admin.username,
        "csrf_token": csrf_token,
    }


@router.get("/me")
async def get_logged_in_admin(
    admin: AdminUser = Depends(get_current_admin),
):
    return {
        "authenticated": True,
        "username": admin.username,
    }


@router.post(
    "/logout",
    dependencies=[Depends(verify_csrf)],
)
async def admin_logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    session_token = request.cookies.get(SESSION_COOKIE_NAME)

    session = await get_admin_session(
        db=db,
        session_token=session_token,
    )

    if session:
        await delete_admin_session(db, session)

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=(os.getenv("APP_ENV", "development").lower() == "production"),
        samesite=(
            "none"
            if os.getenv("APP_ENV", "development").lower() == "production"
            else "lax"
        ),
    )

    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        path="/",
        secure=(os.getenv("APP_ENV", "development").lower() == "production"),
        samesite=(
            "none"
            if os.getenv("APP_ENV", "development").lower() == "production"
            else "lax"
        ),
    )

    return {
        "message": "Logout successful",
    }
