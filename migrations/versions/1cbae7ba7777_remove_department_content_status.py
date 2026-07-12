"""remove_department_content_status

Revision ID: 1cbae7ba7777
Revises: e69dd410fcfe
Create Date: 2026-07-11 21:56:10.893500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1cbae7ba7777'
down_revision: Union[str, None] = 'e69dd410fcfe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop constraint first
    op.drop_constraint('ck_department_content_status', 'departments', type_='check')
    # Drop column
    op.drop_column('departments', 'content_status')


def downgrade() -> None:
    op.add_column('departments', sa.Column('content_status', sa.String(length=30), server_default=sa.text("'draft'"), nullable=False))
    op.create_check_constraint(
        "ck_department_content_status",
        "departments",
        "content_status IN ('draft', 'review', 'published')",
    )
