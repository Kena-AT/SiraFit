"""Add user_sessions and session_access_logs tables (Sprint 5)

Revision ID: 20260917_001
Revises: 20260910_001
Create Date: 2026-09-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260917_001"
down_revision: Union[str, Sequence[str], None] = "20260910_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. user_sessions table
    if "user_sessions" not in existing_tables:
        op.create_table(
            "user_sessions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("platform", sa.String(50), nullable=False),
            sa.Column("encrypted_session_data", sa.Text(), nullable=False),
            sa.Column("stored_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
        op.create_index("ix_user_sessions_platform", "user_sessions", ["platform"])
        op.create_index(
            "ix_user_sessions_user_platform_active",
            "user_sessions",
            ["user_id", "platform", "is_active"],
        )

    # 2. session_access_logs table
    if "session_access_logs" not in existing_tables:
        op.create_table(
            "session_access_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("platform", sa.String(50), nullable=False),
            sa.Column("action", sa.String(50), nullable=False),
            sa.Column("result", sa.String(50), nullable=False),
            sa.Column("error_code", sa.String(100), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_session_access_logs_user_id", "session_access_logs", ["user_id"])
        op.create_index("ix_session_access_logs_platform", "session_access_logs", ["platform"])
        op.create_index("ix_session_access_logs_created_at", "session_access_logs", ["created_at"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "session_access_logs" in existing_tables:
        op.drop_table("session_access_logs")

    if "user_sessions" in existing_tables:
        op.drop_table("user_sessions")
