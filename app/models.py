from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
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


class ClientEngagementEvent(Base):
    __tablename__ = "client_engagement_events"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    contact_id: Mapped[int] = mapped_column(
        ForeignKey("telegram_contacts.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    previous_value: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    new_value: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    event_source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index(
            "ix_client_engagement_contact_occurred",
            "contact_id",
            "occurred_at",
        ),
        Index(
            "ix_client_engagement_type_occurred",
            "event_type",
            "occurred_at",
        ),
    )


class StrategyCustomer(Base):
    __tablename__ = "strategy_customers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    whatsapp: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    case_notes: Mapped[str | None] = mapped_column(
        String(2000),
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


class StrategyBooking(Base):
    __tablename__ = "strategy_bookings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("strategy_customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    telegram_contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("telegram_contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    booking_reference: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        nullable=False,
        index=True,
    )

    package_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    package_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    amount_ngn: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    session_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending_payment",
        nullable=False,
        index=True,
    )

    access_token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    access_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    access_revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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


class StrategyService(Base):
    __tablename__ = "strategy_services"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    code: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)

    price_ngn: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    session_count: Mapped[int] = mapped_column(Integer, nullable=False)

    features: Mapped[list] = mapped_column(JSON, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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


class StrategySiteSetting(Base):
    __tablename__ = "strategy_site_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    value: Mapped[dict] = mapped_column(JSON, nullable=False)

    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class StrategyContentSection(Base):
    __tablename__ = "strategy_content_sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    section_key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    eyebrow: Mapped[str | None] = mapped_column(String(150), nullable=True)

    body: Mapped[str] = mapped_column(String(5000), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

class StrategyAdminNotification(Base):
    __tablename__ = "strategy_admin_notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # Unique identifier for the business event.
    # Prevents the same event from being queued more than once.
    event_key: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        index=True,
    )

    message: Mapped[str] = mapped_column(
        String(4000),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )

    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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


class StrategyTelegramLinkToken(Base):
    __tablename__ = "strategy_telegram_link_tokens"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    booking_id: Mapped[int] = mapped_column(
        ForeignKey("strategy_bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("strategy_customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # SHA-256 hash only. Never store the original linking code.
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class StrategyTelegramLink(Base):
    __tablename__ = "strategy_telegram_links"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # One Telegram contact per StrategyCustomer record.
    # A Telegram contact may belong to multiple customer records.
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("strategy_customers.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    telegram_contact_id: Mapped[int] = mapped_column(
        ForeignKey("telegram_contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class StrategyCustomerNotification(Base):
    __tablename__ = "strategy_customer_notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("strategy_customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Prevent duplicate notifications for the same business event.
    event_key: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        index=True,
    )

    message: Mapped[str] = mapped_column(
        String(4000),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )

    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
