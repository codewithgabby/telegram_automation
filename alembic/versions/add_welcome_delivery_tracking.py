"""Add welcome delivery tracking.

Revision ID: 7c9f2a1b6d43
Revises: e5c31dced858
"""

from alembic import op
import sqlalchemy as sa

revision = "7c9f2a1b6d43"
down_revision = "e5c31dced858"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "telegram_contacts",
        sa.Column(
            "welcome_status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
    )

    # Preserve the correct status for existing contacts.
    op.execute("""
        UPDATE telegram_contacts
        SET welcome_status = 'sent'
        WHERE welcome_sent_at IS NOT NULL
        """)


def downgrade():
    op.drop_column("telegram_contacts", "welcome_status")
