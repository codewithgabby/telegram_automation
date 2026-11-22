"""Create strategy payment receipts table.

Revision ID: c4e81a72d903
Revises: b83d91f204a6
"""

from alembic import op
import sqlalchemy as sa

revision = "c4e81a72d903"
down_revision = "b83d91f204a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategy_payment_receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "booking_id",
            sa.Integer(),
            sa.ForeignKey("strategy_bookings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("transfer_reference", sa.String(length=150), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="submitted",
        ),
        sa.Column("admin_note", sa.String(length=1000), nullable=True),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "storage_key",
            name="uq_strategy_payment_receipts_storage_key",
        ),
    )

    op.create_index(
        "ix_strategy_payment_receipts_booking_id",
        "strategy_payment_receipts",
        ["booking_id"],
    )

    op.create_index(
        "ix_strategy_payment_receipts_status",
        "strategy_payment_receipts",
        ["status"],
    )

    op.create_index(
        "ix_strategy_receipt_booking_status",
        "strategy_payment_receipts",
        ["booking_id", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_strategy_receipt_booking_status",
        table_name="strategy_payment_receipts",
    )
    op.drop_index(
        "ix_strategy_payment_receipts_status",
        table_name="strategy_payment_receipts",
    )
    op.drop_index(
        "ix_strategy_payment_receipts_booking_id",
        table_name="strategy_payment_receipts",
    )
    op.drop_table("strategy_payment_receipts")
