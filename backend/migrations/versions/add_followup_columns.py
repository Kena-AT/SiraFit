"""add follow_up_at and follow_up_note to job_applications

Revision ID: add_followup_columns
Revises: add_analytics_and_notifications
Create Date: 2026-07-14 12:00:00.000000

Adds two nullable columns to job_applications:
  follow_up_at   — UTC datetime when the user wants a reminder
  follow_up_note — brief label for the reminder (max 500 chars)

Also creates an index on (user_id, follow_up_at) to speed up the
follow-up center query.
"""
from alembic import op
import sqlalchemy as sa

revision = "add_followup_columns"
down_revision = "add_analytics_and_notifications"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "job_applications",
        sa.Column("follow_up_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "job_applications",
        sa.Column("follow_up_note", sa.String(500), nullable=True),
    )
    op.create_index(
        "ix_job_applications_user_followup",
        "job_applications",
        ["user_id", "follow_up_at"],
    )


def downgrade():
    op.drop_index("ix_job_applications_user_followup", table_name="job_applications")
    op.drop_column("job_applications", "follow_up_note")
    op.drop_column("job_applications", "follow_up_at")
