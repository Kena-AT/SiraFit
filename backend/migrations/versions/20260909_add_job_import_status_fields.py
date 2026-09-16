"""Add job import status and async tracking fields.

Revision ID: 20260909_import_status
Revises: 20260820_001
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa

revision = '20260909_import_status'
down_revision = '20260820_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('job_imports', sa.Column('parsed_data', sa.JSON(), nullable=True))
    op.add_column('job_imports', sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    op.drop_column('job_imports', 'processed_at')
    op.drop_column('job_imports', 'parsed_data')
