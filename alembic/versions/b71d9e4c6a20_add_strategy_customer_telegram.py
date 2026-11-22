"""Add Strategy customer Telegram integration tables.

Revision ID: b71d9e4c6a20
Revises: e8b5c21a9f40
"""

from alembic import op
import sqlalchemy as sa

revision = "b71d9e4c6a20"
down_revision = "e8b5c21a9f40"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategy_telegram_link_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "booking_id",
            sa.Integer(),
            sa.ForeignKey("strategy_bookings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("strategy_customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "token_hash",
            name="uq_strategy_telegram_link_token_hash",
        ),
    )

    op.create_index(
        "ix_strategy_telegram_link_tokens_booking_id",
        "strategy_telegram_link_tokens",
        ["booking_id"],
    )
    op.create_index(
        "ix_strategy_telegram_link_tokens_customer_id",
        "strategy_telegram_link_tokens",
        ["customer_id"],
    )
    op.create_index(
        "ix_strategy_telegram_link_tokens_expires_at",
        "strategy_telegram_link_tokens",
        ["expires_at"],
    )

    op.create_table(
        "strategy_telegram_links",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("strategy_customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "telegram_contact_id",
            sa.Integer(),
            sa.ForeignKey("telegram_contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "linked_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "customer_id",
            name="uq_strategy_telegram_link_customer_id",
        ),
    )

    op.create_index(
        "ix_strategy_telegram_links_telegram_contact_id",
        "strategy_telegram_links",
        ["telegram_contact_id"],
    )

    op.create_table(
        "strategy_customer_notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("strategy_customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_key", sa.String(150), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("message", sa.String(4000), nullable=False),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "max_attempts",
            sa.Integer(),
            nullable=False,
            server_default="3",
        ),
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "event_key",
            name="uq_strategy_customer_notification_event_key",
        ),
    )

    op.create_index(
        "ix_strategy_customer_notifications_customer_id",
        "strategy_customer_notifications",
        ["customer_id"],
    )
    op.create_index(
        "ix_strategy_customer_notifications_event_type",
        "strategy_customer_notifications",
        ["event_type"],
    )
    op.create_index(
        "ix_strategy_customer_notifications_status",
        "strategy_customer_notifications",
        ["status"],
    )
    op.create_index(
        "ix_strategy_customer_notifications_available_at",
        "strategy_customer_notifications",
        ["available_at"],
    )


def downgrade() -> None:
    op.drop_table("strategy_customer_notifications")

    op.drop_index(
        "ix_strategy_telegram_links_telegram_contact_id",
        table_name="strategy_telegram_links",
    )
    op.drop_table("strategy_telegram_links")

    op.drop_index(
        "ix_strategy_telegram_link_tokens_expires_at",
        table_name="strategy_telegram_link_tokens",
    )
    op.drop_index(
        "ix_strategy_telegram_link_tokens_customer_id",
        table_name="strategy_telegram_link_tokens",
    )
    op.drop_index(
        "ix_strategy_telegram_link_tokens_booking_id",
        table_name="strategy_telegram_link_tokens",
    )
    op.drop_table("strategy_telegram_link_tokens")
