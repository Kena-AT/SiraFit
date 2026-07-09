"""add application tracking tables

Revision ID: add_application_tracking
Revises: add_cover_letters_table
Create Date: 2026-07-09 10:00:00.000000

Adds tables for Sprint 9 (Application Tracking):

  application_events   — chronological timeline events per application
  application_notes    — user-authored notes per application
  application_contacts — recruiter/HR contacts per application

Also adds an ``ix_job_applications_user_status`` composite index on the
existing ``job_applications`` table to speed up the Kanban board query
(``WHERE user_id = ? GROUP BY status``).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "add_application_tracking"
down_revision = "add_cover_letters_table"
branch_labels = None
depends_on = None


def upgrade():
    # ---------------------------------------------------------------------
    # application_events (timeline)
    # ---------------------------------------------------------------------
    op.create_table(
        "application_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # status_change | note | email | interview | offer | reminder | system
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Free-form structured data (from_status/to_status, kind, etc.)
        sa.Column("event_metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_application_events_user_id", "application_events", ["user_id"])
    op.create_index("ix_application_events_app_id", "application_events", ["application_id"])
    op.create_index("ix_application_events_occurred_at", "application_events", ["occurred_at"])
    op.create_index("ix_application_events_user_app", "application_events", ["user_id", "application_id"])

    # ---------------------------------------------------------------------
    # application_notes
    # ---------------------------------------------------------------------
    op.create_table(
        "application_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("author", sa.String(100), nullable=True),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_application_notes_user_id", "application_notes", ["user_id"])
    op.create_index("ix_application_notes_app_id", "application_notes", ["application_id"])
    op.create_index("ix_application_notes_user_app", "application_notes", ["user_id", "application_id"])

    # ---------------------------------------------------------------------
    # application_contacts
    # ---------------------------------------------------------------------
    op.create_table(
        "application_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        # recruiter | hiring_manager | hr | referrer | interviewer | other
        sa.Column("role", sa.String(50), nullable=False, server_default="recruiter"),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("linkedin", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_application_contacts_user_id", "application_contacts", ["user_id"])
    op.create_index("ix_application_contacts_app_id", "application_contacts", ["application_id"])
    op.create_index("ix_application_contacts_user_app", "application_contacts", ["user_id", "application_id"])

    # ---------------------------------------------------------------------
    # Indexes on existing job_applications to speed up Kanban / list queries
    # ---------------------------------------------------------------------
    op.create_index("ix_job_applications_user_status", "job_applications", ["user_id", "status"])
    op.create_index("ix_job_applications_user_job", "job_applications", ["user_id", "job_id"], unique=True)


def downgrade():
    op.drop_index("ix_job_applications_user_job", table_name="job_applications")
    op.drop_index("ix_job_applications_user_status", table_name="job_applications")

    op.drop_index("ix_application_contacts_user_app", table_name="application_contacts")
    op.drop_index("ix_application_contacts_app_id", table_name="application_contacts")
    op.drop_index("ix_application_contacts_user_id", table_name="application_contacts")
    op.drop_table("application_contacts")

    op.drop_index("ix_application_notes_user_app", table_name="application_notes")
    op.drop_index("ix_application_notes_app_id", table_name="application_notes")
    op.drop_index("ix_application_notes_user_id", table_name="application_notes")
    op.drop_table("application_notes")

    op.drop_index("ix_application_events_user_app", table_name="application_events")
    op.drop_index("ix_application_events_occurred_at", table_name="application_events")
    op.drop_index("ix_application_events_app_id", table_name="application_events")
    op.drop_index("ix_application_events_user_id", table_name="application_events")
    op.drop_table("application_events")
