"""Add dynamic Strategy Session packages and website content.

Revision ID: b83d91f204a6
Revises: 91a7c4e82b10
"""

from alembic import op
import sqlalchemy as sa

revision = "b83d91f204a6"
down_revision = "91a7c4e82b10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategy_services",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(30), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column("price_ngn", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("session_count", sa.Integer(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_strategy_services_code", "strategy_services", ["code"])

    op.create_table(
        "strategy_site_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_strategy_site_settings_key",
        "strategy_site_settings",
        ["key"],
    )

    op.create_table(
        "strategy_content_sections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("section_key", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("eyebrow", sa.String(150), nullable=True),
        sa.Column("body", sa.String(5000), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_strategy_content_sections_section_key",
        "strategy_content_sections",
        ["section_key"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_strategy_content_sections_section_key",
        table_name="strategy_content_sections",
    )
    op.drop_table("strategy_content_sections")

    op.drop_index(
        "ix_strategy_site_settings_key",
        table_name="strategy_site_settings",
    )
    op.drop_table("strategy_site_settings")

    op.drop_index("ix_strategy_services_code", table_name="strategy_services")
    op.drop_table("strategy_services")
