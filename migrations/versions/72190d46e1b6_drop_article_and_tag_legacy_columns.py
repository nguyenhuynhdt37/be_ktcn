"""drop_article_and_tag_legacy_columns

Revision ID: 72190d46e1b6
Revises: 4795ce8eda29
Create Date: 2026-07-01 18:50:28.691672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72190d46e1b6'
down_revision: Union[str, None] = '4795ce8eda29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop columns trong bảng articles
    op.drop_column('articles', 'title')
    op.drop_column('articles', 'slug')
    op.drop_column('articles', 'excerpt')
    op.drop_column('articles', 'content')
    op.drop_column('articles', 'seo_title')
    op.drop_column('articles', 'seo_description')
    op.drop_column('articles', 'canonical_url')
    op.drop_column('articles', 'robots')
    op.drop_column('articles', 'og_title')
    op.drop_column('articles', 'og_description')
    op.drop_column('articles', 'og_image')

    # 2. Drop columns trong bảng tags
    op.drop_column('tags', 'name')
    op.drop_column('tags', 'slug')
    op.drop_column('tags', 'description')


def downgrade() -> None:
    # 1. Add lại columns cho bảng articles
    op.add_column('articles', sa.Column('title', sa.String(255), nullable=True))
    op.add_column('articles', sa.Column('slug', sa.String(255), nullable=True, unique=True))
    op.add_column('articles', sa.Column('excerpt', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('content', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('seo_title', sa.String(255), nullable=True))
    op.add_column('articles', sa.Column('seo_description', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('canonical_url', sa.String(255), nullable=True))
    op.add_column('articles', sa.Column('robots', sa.String(50), nullable=True))
    op.add_column('articles', sa.Column('og_title', sa.String(255), nullable=True))
    op.add_column('articles', sa.Column('og_description', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('og_image', sa.String(512), nullable=True))

    # 2. Add lại columns cho bảng tags
    op.add_column('tags', sa.Column('name', sa.String(255), nullable=True))
    op.add_column('tags', sa.Column('slug', sa.String(255), nullable=True, unique=True))
    op.add_column('tags', sa.Column('description', sa.Text(), nullable=True))
