"""remove_department_translation_short_description

Revision ID: fbf2c440aade
Revises: 1cbae7ba7777
Create Date: 2026-07-11 22:44:34.058169

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fbf2c440aade'
down_revision: Union[str, None] = '1cbae7ba7777'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('department_translations', 'short_description')


def downgrade() -> None:
    op.add_column('department_translations', sa.Column('short_description', sa.Text(), nullable=True))
