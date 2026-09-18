"""add ws_connection_logs

Revision ID: 20260917_009
Revises: 20260917_008
Create Date: 2026-09-17 21:38:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20260917_009'
down_revision = '20260917_008'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ws_connection_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("event", sa.String(20), nullable=False),
        sa.Column("reason", sa.String(50)),
        sa.Column("duration_sec", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ws_connection_logs_user_id", "ws_connection_logs", ["user_id"])


def downgrade():
    op.drop_index("ix_ws_connection_logs_user_id", table_name="ws_connection_logs")
    op.drop_table("ws_connection_logs")
