"""Add Strategy Session administrator notifications.

Revision ID: e8b5c21a9f40
Revises: d7a4c91e2f60
"""

from alembic import op
import sqlalchemy as sa

revision = "e8b5c21a9f40"
down_revision = "d7a4c91e2f60"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategy_admin_notifications",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "event_key",
            sa.String(150),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(60),
            nullable=False,
        ),
        sa.Column(
            "message",
            sa.String(4000),
            nullable=False,
        ),
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
        sa.Column(
            "locked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_error",
            sa.String(1000),
            nullable=True,
        ),
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
            name="uq_strategy_admin_notification_event_key",
        ),
    )

    op.create_index(
        "ix_strategy_admin_notifications_event_type",
        "strategy_admin_notifications",
        ["event_type"],
    )

    op.create_index(
        "ix_strategy_admin_notifications_status",
        "strategy_admin_notifications",
        ["status"],
    )

    op.create_index(
        "ix_strategy_admin_notifications_available_at",
        "strategy_admin_notifications",
        ["available_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_strategy_admin_notifications_available_at",
        table_name="strategy_admin_notifications",
    )

    op.drop_index(
        "ix_strategy_admin_notifications_status",
        table_name="strategy_admin_notifications",
    )

    op.drop_index(
        "ix_strategy_admin_notifications_event_type",
        table_name="strategy_admin_notifications",
    )

    op.drop_table("strategy_admin_notifications")
