"""add batch jobs table

Revision ID: add_batch_jobs_table
Revises: add_application_tracking
Create Date: 2026-07-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "add_batch_jobs_table"
down_revision = "add_application_tracking"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "batch_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("succeeded_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_batch_jobs_user_status", "batch_jobs", ["user_id", "status"])
    op.create_index("ix_batch_jobs_user_type", "batch_jobs", ["user_id", "operation_type"])
    op.create_index("ix_batch_jobs_created", "batch_jobs", ["created_at"])


def downgrade():
    op.drop_index("ix_batch_jobs_created", table_name="batch_jobs")
    op.drop_index("ix_batch_jobs_user_type", table_name="batch_jobs")
    op.drop_index("ix_batch_jobs_user_status", table_name="batch_jobs")
    op.drop_table("batch_jobs")