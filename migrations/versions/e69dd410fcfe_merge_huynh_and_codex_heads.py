"""merge huynh and codex heads

Revision ID: e69dd410fcfe
Revises: 2a7d9f4c6e11, 5f24a2e9463a
Create Date: 2026-07-11 19:55:30.126183

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e69dd410fcfe'
down_revision: Union[str, None] = ('2a7d9f4c6e11', '5f24a2e9463a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
