"""add_article_id_to_banners

Revision ID: eafd9139cecc
Revises: d484c2dee627
Create Date: 2026-07-12 13:36:03.244553

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eafd9139cecc'
down_revision: Union[str, None] = 'd484c2dee627'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Thêm cột article_id và tạo khóa ngoại tới bảng articles
    op.add_column('banners', sa.Column('article_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_banners_article_id', 'banners', 'articles', ['article_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # 1. Xóa khóa ngoại và cột article_id
    op.drop_constraint('fk_banners_article_id', 'banners', type_='foreignkey')
    op.drop_column('banners', 'article_id')
