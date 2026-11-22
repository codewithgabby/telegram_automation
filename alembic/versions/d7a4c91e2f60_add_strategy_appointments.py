"""Add Strategy Session availability and appointments.

Revision ID: d7a4c91e2f60
Revises: c4e81a72d903
"""

from datetime import time

from alembic import op
import sqlalchemy as sa

revision = "d7a4c91e2f60"
down_revision = "c4e81a72d903"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------
    # Availability windows
    # -----------------------------------------------------

    op.create_table(
        "strategy_availability_windows",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
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

    # Default availability: Monday through Sunday, 9 AM–8 PM.
    availability_table = sa.table(
        "strategy_availability_windows",
        sa.column("weekday", sa.Integer()),
        sa.column("start_time", sa.Time()),
        sa.column("end_time", sa.Time()),
        sa.column("is_active", sa.Boolean()),
    )

    op.bulk_insert(
        availability_table,
        [
            {
                "weekday": weekday,
                "start_time": time(9, 0),
                "end_time": time(20, 0),
                "is_active": True,
            }
            for weekday in range(7)
        ],
    )

    # -----------------------------------------------------
    # Availability blocks
    # -----------------------------------------------------

    op.create_table(
        "strategy_availability_blocks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "start_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "end_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
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

    # -----------------------------------------------------
    # Appointments
    # -----------------------------------------------------

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
        sa.Column(
            "starts_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "ends_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "customer_timezone",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="confirmed",
        ),
        sa.Column(
            "cancellation_reason",
            sa.String(length=500),
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

    # A cancelled appointment releases its slot.
    # Any other appointment status reserves that start time.
    op.create_index(
        "uq_strategy_active_appointment_start",
        "strategy_appointments",
        ["starts_at"],
        unique=True,
        postgresql_where=sa.text("status <> 'cancelled'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_strategy_active_appointment_start",
        table_name="strategy_appointments",
    )

    op.drop_index(
        "ix_strategy_appointments_status",
        table_name="strategy_appointments",
    )

    op.drop_index(
        "ix_strategy_appointments_customer_id",
        table_name="strategy_appointments",
    )

    op.drop_index(
        "ix_strategy_appointments_booking_id",
        table_name="strategy_appointments",
    )

    op.drop_table("strategy_appointments")

    op.drop_index(
        "ix_strategy_availability_block_active_range",
        table_name="strategy_availability_blocks",
    )

    op.drop_index(
        "ix_strategy_availability_blocks_start_at",
        table_name="strategy_availability_blocks",
    )

    op.drop_table("strategy_availability_blocks")

    op.drop_index(
        "ix_strategy_availability_windows_weekday",
        table_name="strategy_availability_windows",
    )

    op.drop_table("strategy_availability_windows")
