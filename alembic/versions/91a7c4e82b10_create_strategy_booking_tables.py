"""Create Strategy Session customer and booking tables.

Revision ID: 91a7c4e82b10
Revises: 4ab6910f5d24
"""

from alembic import op
import sqlalchemy as sa

revision = "91a7c4e82b10"
down_revision = "4ab6910f5d24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategy_customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("whatsapp", sa.String(length=20), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("case_notes", sa.String(length=2000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_strategy_customers_email",
        "strategy_customers",
        ["email"],
    )

    op.create_table(
        "strategy_bookings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("booking_reference", sa.String(length=40), nullable=False),
        sa.Column("package_code", sa.String(length=30), nullable=False),
        sa.Column("package_name", sa.String(length=150), nullable=False),
        sa.Column("amount_ngn", sa.Integer(), nullable=False),
        sa.Column("session_count", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="pending_payment",
        ),
        sa.Column("access_token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "access_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "access_revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["strategy_customers.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_reference"),
        sa.UniqueConstraint("access_token_hash"),
    )

    op.create_index(
        "ix_strategy_bookings_customer_id",
        "strategy_bookings",
        ["customer_id"],
    )
    op.create_index(
        "ix_strategy_bookings_booking_reference",
        "strategy_bookings",
        ["booking_reference"],
    )
    op.create_index(
        "ix_strategy_bookings_status",
        "strategy_bookings",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_strategy_bookings_status",
        table_name="strategy_bookings",
    )
    op.drop_index(
        "ix_strategy_bookings_booking_reference",
        table_name="strategy_bookings",
    )
    op.drop_index(
        "ix_strategy_bookings_customer_id",
        table_name="strategy_bookings",
    )
    op.drop_table("strategy_bookings")

    op.drop_index(
        "ix_strategy_customers_email",
        table_name="strategy_customers",
    )
    op.drop_table("strategy_customers")
