"""Add device_sessions table for tracking user device sessions

Revision ID: 20260730_100700
Revises: 20260730_100500
Create Date: 2026-07-30

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = "20260730_100700"
down_revision = "20260730_100500"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "device_sessions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_name", sa.String(100), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("last_seen", sa.DateTime, default=datetime.utcnow, nullable=False),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow, nullable=False),
    )
    op.create_index("ix_device_sessions_user_active", "device_sessions", ["user_id", "is_active"])


def downgrade():
    op.drop_index("ix_device_sessions_user_active", table_name="device_sessions")
    op.drop_table("device_sessions")
