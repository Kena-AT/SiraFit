"""Add extension_tokens table (Sprint 6)

Revision ID: 20260917_002
Revises: 20260917_001
Create Date: 2026-09-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260917_002"
down_revision: Union[str, Sequence[str], None] = "20260917_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "extension_tokens" not in existing_tables:
        op.create_table(
            "extension_tokens",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column("name", sa.String(100), server_default="Browser Extension", nullable=False),
            sa.Column("is_revoked", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

        op.create_index(
            "ix_extension_tokens_user_id",
            "extension_tokens",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            "ix_extension_tokens_token_hash",
            "extension_tokens",
            ["token_hash"],
            unique=True,
        )
        op.create_index(
            "ix_extension_tokens_is_revoked",
            "extension_tokens",
            ["is_revoked"],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "extension_tokens" in existing_tables:
        op.drop_index("ix_extension_tokens_is_revoked", table_name="extension_tokens")
        op.drop_index("ix_extension_tokens_token_hash", table_name="extension_tokens")
        op.drop_index("ix_extension_tokens_user_id", table_name="extension_tokens")
        op.drop_table("extension_tokens")
