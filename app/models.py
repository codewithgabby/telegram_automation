from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    JSON,
    String,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TelegramContact(Base):
    __tablename__ = "telegram_contacts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
    )

    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    last_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    business_connection_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    welcome_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    welcome_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )

    last_incoming_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    payment_status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    session_status: Mapped[str] = mapped_column(
        String(30),
        default="not_booked",
        nullable=False,
    )

    follow_up_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


class ClientFollowUp(Base):
    __tablename__ = "client_follow_ups"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    contact_id: Mapped[int] = mapped_column(
        ForeignKey("telegram_contacts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    response: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    last_error: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class GroupFAQLink(Base):
    __tablename__ = "group_faq_links"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    topic: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    keywords: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )

    message_link: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    admin_user_id: Mapped[int] = mapped_column(
        ForeignKey("admin_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (Index("ix_admin_sessions_expires_at", "expires_at"),)


class TelegramWebhookEvent(Base):
    __tablename__ = "telegram_webhook_events"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    update_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    webhook_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="processing",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "update_id",
            "webhook_type",
            name="uq_telegram_webhook_update_scope",
        ),
    )
