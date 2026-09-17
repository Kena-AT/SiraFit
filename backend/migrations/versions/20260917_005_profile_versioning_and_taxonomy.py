"""Add profile revision, profile_versions table, and skill_taxonomy table (Sprint 2)

Revision ID: 20260917_005
Revises: 20260917_004
Create Date: 2026-09-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "20260917_005"
down_revision: Union[str, Sequence[str], None] = "20260917_004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Add revision to profiles if present
    if "profiles" in existing_tables:
        profile_cols = {c["name"] for c in inspector.get_columns("profiles")}
        if "revision" not in profile_cols:
            op.add_column(
                "profiles",
                sa.Column(
                    "revision",
                    sa.Integer,
                    nullable=False,
                    server_default=sa.text("1"),
                ),
            )

    # 2. Create profile_versions table if not exists
    if "profile_versions" not in existing_tables:
        op.create_table(
            "profile_versions",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("version", sa.Integer, nullable=False),
            sa.Column("data", sa.JSON, nullable=False),
            sa.Column("source", sa.String(50), nullable=False, server_default="update"),
            sa.Column("reverted_from_version_id", UUID(as_uuid=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint("user_id", "version", name="uq_profile_versions_user_version"),
        )
        op.create_index(
            "ix_profile_versions_user_id_version",
            "profile_versions",
            ["user_id", "version"],
        )

    # 3. Create skill_taxonomy table if not exists
    if "skill_taxonomy" not in existing_tables:
        op.create_table(
            "skill_taxonomy",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("canonical_key", sa.String(100), nullable=False, unique=True, index=True),
            sa.Column("name", sa.String(100), nullable=False, unique=True),
            sa.Column("category", sa.String(50), nullable=False),
            sa.Column("aliases", sa.JSON, nullable=False, server_default="[]"),
            sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "skill_taxonomy" in existing_tables:
        op.drop_table("skill_taxonomy")

    if "profile_versions" in existing_tables:
        op.drop_table("profile_versions")

    if "profiles" in existing_tables:
        profile_cols = {c["name"] for c in inspector.get_columns("profiles")}
        if "revision" in profile_cols:
            op.drop_column("profiles", "revision")
