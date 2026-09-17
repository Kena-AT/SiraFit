"""Harden auth with TOTP is_confirmed and OAuth unique constraints (Sprint 1)

Revision ID: 20260917_004
Revises: 20260917_003
Create Date: 2026-09-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "20260917_004"
down_revision: Union[str, Sequence[str], None] = "20260917_003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Add is_confirmed column to totp_secrets if not present
    if "totp_secrets" in existing_tables:
        totp_cols = {c["name"] for c in inspector.get_columns("totp_secrets")}
        if "is_confirmed" not in totp_cols:
            op.add_column(
                "totp_secrets",
                sa.Column(
                    "is_confirmed",
                    sa.Boolean,
                    nullable=False,
                    server_default=sa.text("true"),  # Existing records treated as confirmed
                ),
            )

    # 2. Add unique constraint (user_id, provider) to oauth_accounts if table exists
    if "oauth_accounts" in existing_tables:
        constraints = {
            c["name"] for c in inspector.get_unique_constraints("oauth_accounts")
        }
        if "uq_oauth_user_provider" not in constraints:
            try:
                op.create_unique_constraint(
                    "uq_oauth_user_provider",
                    "oauth_accounts",
                    ["user_id", "provider"],
                )
            except Exception:
                pass


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "oauth_accounts" in existing_tables:
        constraints = {
            c["name"] for c in inspector.get_unique_constraints("oauth_accounts")
        }
        if "uq_oauth_user_provider" in constraints:
            try:
                op.drop_constraint("uq_oauth_user_provider", "oauth_accounts", type_="unique")
            except Exception:
                pass

    if "totp_secrets" in existing_tables:
        totp_cols = {c["name"] for c in inspector.get_columns("totp_secrets")}
        if "is_confirmed" in totp_cols:
            op.drop_column("totp_secrets", "is_confirmed")
