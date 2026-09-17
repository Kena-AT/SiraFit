"""Add ai_completions and ai_completion_attempts tables (Sprint 7)

Revision ID: 20260917_003
Revises: 20260917_002
Create Date: 2026-09-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260917_003"
down_revision: Union[str, Sequence[str], None] = "20260917_002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "ai_completions" not in existing_tables:
        op.create_table(
            "ai_completions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("generation_id", sa.String(64), nullable=False),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("operation", sa.String(64), nullable=False),
            sa.Column("provider", sa.String(64), nullable=False),
            sa.Column("model", sa.String(128), nullable=False),
            sa.Column("response_model", sa.String(128), nullable=False),
            sa.Column("status", sa.String(32), server_default="success", nullable=False),
            sa.Column("attempt_count", sa.Integer(), server_default="1", nullable=False),
            sa.Column("duration_ms", sa.Integer(), server_default="0", nullable=False),
            sa.Column("total_tokens", sa.Integer(), nullable=True),
            sa.Column("prompt_tokens", sa.Integer(), nullable=True),
            sa.Column("completion_tokens", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )

        op.create_index(
            "ix_ai_completions_generation_id",
            "ai_completions",
            ["generation_id"],
            unique=False,
        )
        op.create_index(
            "ix_ai_completions_user_id",
            "ai_completions",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            "ix_ai_completions_operation",
            "ai_completions",
            ["operation"],
            unique=False,
        )

    if "ai_completion_attempts" not in existing_tables:
        op.create_table(
            "ai_completion_attempts",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "completion_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("ai_completions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("attempt_number", sa.Integer(), server_default="1", nullable=False),
            sa.Column("provider", sa.String(64), nullable=False),
            sa.Column("model", sa.String(128), nullable=False),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("failure_code", sa.String(64), nullable=True),
            sa.Column("validation_errors", sa.JSON(), nullable=True),
            sa.Column("duration_ms", sa.Integer(), server_default="0", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

        op.create_index(
            "ix_ai_completion_attempts_completion_id",
            "ai_completion_attempts",
            ["completion_id"],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "ai_completion_attempts" in existing_tables:
        op.drop_index("ix_ai_completion_attempts_completion_id", table_name="ai_completion_attempts")
        op.drop_table("ai_completion_attempts")

    if "ai_completions" in existing_tables:
        op.drop_index("ix_ai_completions_operation", table_name="ai_completions")
        op.drop_index("ix_ai_completions_user_id", table_name="ai_completions")
        op.drop_index("ix_ai_completions_generation_id", table_name="ai_completions")
        op.drop_table("ai_completions")
