"""Add market_trend_history table for tracking historical market data

Revision ID: 20260730_100500
Revises: 20260730_100300
Create Date: 2026-07-30

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = "20260730_100500"
down_revision = "20260730_100300"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "market_trend_history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("period_start", sa.DateTime, nullable=False),
        sa.Column("period_end", sa.DateTime, nullable=False),
        sa.Column("total_jobs", sa.Integer, default=0),
        sa.Column("avg_salary", sa.Numeric(12, 2)),
        sa.Column("top_skills", sa.JSON),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow),
    )
    op.create_index(
        "ix_market_trend_period",
        "market_trend_history",
        ["period_start", "period_end"],
    )


def downgrade():
    op.drop_index("ix_market_trend_period", table_name="market_trend_history")
    op.drop_table("market_trend_history")
