"""merge huynh and codex heads

Revision ID: 38171cc369dc
Revises: 29bbea4da158, b84f90d2a1e3
Create Date: 2026-07-06 20:51:23.245842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38171cc369dc'
down_revision: Union[str, None] = ('29bbea4da158', 'b84f90d2a1e3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
