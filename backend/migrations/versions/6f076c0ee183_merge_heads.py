"""Merge heads

Revision ID: 6f076c0ee183
Revises: 20260812_001, 4e8ef71af25f, add_resumes_user_id_index
Create Date: 2026-08-18 11:58:30.348983+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f076c0ee183'
down_revision: Union[str, None] = ('20260812_001', '4e8ef71af25f', 'add_resumes_user_id_index')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
