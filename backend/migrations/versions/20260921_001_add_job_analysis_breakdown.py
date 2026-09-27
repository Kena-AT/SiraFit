"""add job analysis breakdown and resume compatibility columns

Revision ID: 20260921_001
Revises: 20260918_001
Create Date: 2026-09-21 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260921_001'
down_revision = '20260918_001'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # Add columns safely
    op.add_column('job_analysis', sa.Column('role_overview', sa.Text(), nullable=True))
    op.add_column('job_analysis', sa.Column('core_responsibilities', sa.JSON(), nullable=True))
    op.add_column('job_analysis', sa.Column('required_qualifications', sa.JSON(), nullable=True))
    op.add_column('job_analysis', sa.Column('nice_to_have', sa.JSON(), nullable=True))
    op.add_column('job_analysis', sa.Column('compensation_notes', sa.Text(), nullable=True))
    op.add_column('job_analysis', sa.Column('fit_verdict', sa.String(length=100), nullable=True))
    op.add_column('job_analysis', sa.Column('tailoring_recommendations', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('job_analysis', 'tailoring_recommendations')
    op.drop_column('job_analysis', 'fit_verdict')
    op.drop_column('job_analysis', 'compensation_notes')
    op.drop_column('job_analysis', 'nice_to_have')
    op.drop_column('job_analysis', 'required_qualifications')
    op.drop_column('job_analysis', 'core_responsibilities')
    op.drop_column('job_analysis', 'role_overview')
