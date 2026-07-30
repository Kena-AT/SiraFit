"""Add rejection_stage to JobApplication

Revision ID: 20260730_100300
Revises: 20260730_100141
Create Date: 2026-07-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260730_100300"
down_revision = "20260730_100141"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("job_applications") as batch:
        batch.add_column(sa.Column("rejection_stage", sa.String(30), nullable=True))
    op.create_index("ix_job_applications_rejection_stage", "job_applications", ["rejection_stage"])


def downgrade():
    op.drop_index("ix_job_applications_rejection_stage", table_name="job_applications")
    with op.batch_alter_table("job_applications") as batch:
        batch.drop_column("rejection_stage")
