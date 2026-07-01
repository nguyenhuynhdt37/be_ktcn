"""remove_menu_item_icon

Revision ID: 647478ff8670
Revises: 46c084449deb
Create Date: 2026-07-01 11:53:33.814339

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '647478ff8670'
down_revision: Union[str, None] = '46c084449deb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('menu_items', 'icon')


def downgrade() -> None:
    op.add_column('menu_items', sa.Column('icon', sa.String(length=100), nullable=True))
