import hashlib
import secrets
from datetime import datetime, timedelta

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AdminUser, AdminSession

password_hash = PasswordHash.recommended()

SESSION_DURATION_HOURS = 12


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(password, hashed_password)


async def create_admin_user(
    db: AsyncSession,
    username: str,
    password: str,
) -> AdminUser:
    admin = AdminUser(
        username=username,
        password_hash=hash_password(password),
    )

    db.add(admin)
    await db.commit()
    await db.refresh(admin)

    return admin


async def authenticate_admin(
    db: AsyncSession,
    username: str,
    password: str,
) -> AdminUser | None:
    result = await db.execute(select(AdminUser).where(AdminUser.username == username))

    admin = result.scalar_one_or_none()

    if not admin or not admin.is_active:
        return None

    if not verify_password(
        password,
        admin.password_hash,
    ):
        return None

    return admin


async def create_admin_session(
    db: AsyncSession,
    admin_user_id: int,
) -> tuple[str, AdminSession]:
    session_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(session_token.encode()).hexdigest()

    session = AdminSession(
        admin_user_id=admin_user_id,
        session_token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS),
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session_token, session


async def get_admin_session(
    db: AsyncSession,
    session_token: str,
) -> AdminSession | None:
    token_hash = hashlib.sha256(session_token.encode()).hexdigest()

    result = await db.execute(
        select(AdminSession).where(
            AdminSession.session_token_hash == token_hash,
            AdminSession.expires_at > datetime.utcnow(),
        )
    )

    return result.scalar_one_or_none()


async def delete_admin_session(
    db: AsyncSession,
    session: AdminSession,
) -> None:
    await db.delete(session)
    await db.commit()
