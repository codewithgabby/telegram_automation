"""Remove obsolete Strategy Session receipts and scheduling tables.

Revision ID: a71ae07cac2b
Revises: 573743443d63
"""

from alembic import op
import sqlalchemy as sa

revision = "a71ae07cac2b"
down_revision = "573743443d63"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove appointments first, before their related availability
    # and payment receipt tables.
    op.drop_table("strategy_appointments")
    op.drop_table("strategy_availability_blocks")
    op.drop_table("strategy_availability_windows")
    op.drop_table("strategy_payment_receipts")


def downgrade() -> None:
    # Restore payment receipts.
    op.create_table(
        "strategy_payment_receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "booking_id",
            sa.Integer(),
            sa.ForeignKey("strategy_bookings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("transfer_reference", sa.String(150), nullable=True),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="submitted",
        ),
        sa.Column("admin_note", sa.String(1000), nullable=True),
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

    # Restore availability windows.
    op.create_table(
        "strategy_availability_windows",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        sa.CheckConstraint(
            "weekday >= 0 AND weekday <= 6",
            name="ck_strategy_availability_weekday",
        ),
        sa.CheckConstraint(
            "end_time > start_time",
            name="ck_strategy_availability_time_range",
        ),
        sa.UniqueConstraint(
            "weekday",
            "start_time",
            "end_time",
            name="uq_strategy_availability_window",
        ),
    )
    op.create_index(
        "ix_strategy_availability_windows_weekday",
        "strategy_availability_windows",
        ["weekday"],
    )

    # Restore availability blocks.
    op.create_table(
        "strategy_availability_blocks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "end_at > start_at",
            name="ck_strategy_availability_block_range",
        ),
    )
    op.create_index(
        "ix_strategy_availability_blocks_start_at",
        "strategy_availability_blocks",
        ["start_at"],
    )
    op.create_index(
        "ix_strategy_availability_block_active_range",
        "strategy_availability_blocks",
        ["is_active", "start_at", "end_at"],
    )

    # Restore appointments.
    op.create_table(
        "strategy_appointments",
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
            sa.ForeignKey("strategy_customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("session_number", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("customer_timezone", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="confirmed"),
        sa.Column("cancellation_reason", sa.String(500), nullable=True),
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
        sa.CheckConstraint(
            "session_number >= 1",
            name="ck_strategy_appointment_session_number",
        ),
        sa.CheckConstraint(
            "ends_at > starts_at",
            name="ck_strategy_appointment_time_range",
        ),
        sa.UniqueConstraint(
            "booking_id",
            "session_number",
            name="uq_strategy_booking_session_number",
        ),
    )
    op.create_index(
        "ix_strategy_appointments_booking_id",
        "strategy_appointments",
        ["booking_id"],
    )
    op.create_index(
        "ix_strategy_appointments_customer_id",
        "strategy_appointments",
        ["customer_id"],
    )
    op.create_index(
        "ix_strategy_appointments_status",
        "strategy_appointments",
        ["status"],
    )
    op.create_index(
        "uq_strategy_active_appointment_start",
        "strategy_appointments",
        ["starts_at"],
        unique=True,
        postgresql_where=sa.text("status <> 'cancelled'"),
    )
