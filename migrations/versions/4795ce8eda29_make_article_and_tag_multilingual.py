"""make_article_and_tag_multilingual

Revision ID: 4795ce8eda29
Revises: 0dc542f085e0
Create Date: 2026-07-01 18:30:35.852062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4795ce8eda29'
down_revision: Union[str, None] = '0dc542f085e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tạo bảng article_translations
    op.create_table(
        'article_translations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('article_id', sa.UUID(), nullable=False),
        sa.Column('language_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('seo_title', sa.String(length=255), nullable=True),
        sa.Column('seo_description', sa.Text(), nullable=True),
        sa.Column('canonical_url', sa.String(length=255), nullable=True),
        sa.Column('robots', sa.String(length=50), nullable=True),
        sa.Column('og_title', sa.String(length=255), nullable=True),
        sa.Column('og_description', sa.Text(), nullable=True),
        sa.Column('og_image', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_id', 'language_id', name='uq_article_language_unique'),
        sa.UniqueConstraint('language_id', 'slug', name='uq_article_language_slug_unique')
    )
    op.create_index('ix_article_translations_article_language', 'article_translations', ['article_id', 'language_id'], unique=False)
    op.create_index('ix_article_translations_language_slug', 'article_translations', ['language_id', 'slug'], unique=False)

    # 2. Tạo bảng tag_translations
    op.create_table(
        'tag_translations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.Column('language_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tag_id', 'language_id', name='uq_tag_language_unique'),
        sa.UniqueConstraint('language_id', 'slug', name='uq_tag_language_slug_unique')
    )
    op.create_index('ix_tag_translations_tag_language', 'tag_translations', ['tag_id', 'language_id'], unique=False)
    op.create_index('ix_tag_translations_language_slug', 'tag_translations', ['language_id', 'slug'], unique=False)

    # 3. Chạy Data Migration bằng Python
    bind = op.get_bind()
    # Lấy language_id của vi
    lang_id = bind.execute(sa.text("SELECT id FROM languages WHERE code = 'vi'")).scalar()
    if lang_id:
        # Migrate Article
        articles = bind.execute(sa.text("""
            SELECT id, title, slug, excerpt, content, seo_title, seo_description, 
                   canonical_url, robots, og_title, og_description, og_image, 
                   created_at, updated_at 
            FROM articles
        """)).fetchall()
        for art in articles:
            import uuid
            trans_id = uuid.uuid4()
            bind.execute(
                sa.text("""
                    INSERT INTO article_translations (
                        id, article_id, language_id, title, slug, excerpt, content,
                        seo_title, seo_description, canonical_url, robots,
                        og_title, og_description, og_image, created_at, updated_at
                    ) VALUES (
                        :id, :article_id, :language_id, :title, :slug, :excerpt, :content,
                        :seo_title, :seo_description, :canonical_url, :robots,
                        :og_title, :og_description, :og_image, :created_at, :updated_at
                    )
                """),
                {
                    "id": trans_id,
                    "article_id": art.id,
                    "language_id": lang_id,
                    "title": art.title,
                    "slug": art.slug,
                    "excerpt": art.excerpt,
                    "content": art.content,
                    "seo_title": art.seo_title,
                    "seo_description": art.seo_description,
                    "canonical_url": art.canonical_url,
                    "robots": art.robots,
                    "og_title": art.og_title,
                    "og_description": art.og_description,
                    "og_image": art.og_image,
                    "created_at": art.created_at,
                    "updated_at": art.updated_at
                }
             )

        # Migrate Tag
        tags = bind.execute(sa.text("SELECT id, name, slug, description, created_at, updated_at FROM tags")).fetchall()
        for t in tags:
            import uuid
            trans_id = uuid.uuid4()
            bind.execute(
                sa.text("""
                    INSERT INTO tag_translations (
                        id, tag_id, language_id, name, slug, description, created_at, updated_at
                    ) VALUES (
                        :id, :tag_id, :language_id, :name, :slug, :description, :created_at, :updated_at
                    )
                """),
                {
                    "id": trans_id,
                    "tag_id": t.id,
                    "language_id": lang_id,
                    "name": t.name,
                    "slug": t.slug,
                    "description": t.description,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at
                }
            )


def downgrade() -> None:
    op.drop_index('ix_tag_translations_language_slug', table_name='tag_translations')
    op.drop_index('ix_tag_translations_tag_language', table_name='tag_translations')
    op.drop_table('tag_translations')

    op.drop_index('ix_article_translations_language_slug', table_name='article_translations')
    op.drop_index('ix_article_translations_article_language', table_name='article_translations')
    op.drop_table('article_translations')
