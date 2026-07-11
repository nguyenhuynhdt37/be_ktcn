"""add programs, galleries and article links

Revision ID: 2a7d9f4c6e11
Revises: 8f6c2d1a4b90
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "2a7d9f4c6e11"
down_revision: Union[str, None] = "8f6c2d1a4b90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def base_columns():
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "programs", *base_columns(),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("degree_level", sa.String(50), server_default="bachelor", nullable=False),
        sa.Column("duration_years", sa.Numeric(3, 1), nullable=True),
        sa.Column("training_mode", sa.String(100), nullable=True),
        sa.Column("thumbnail_object_key", sa.String(512), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("code")
    )
    op.create_index("ix_programs_department_id", "programs", ["department_id"])
    op.create_index("ix_programs_is_published", "programs", ["is_published"])
    op.create_index("ix_programs_deleted_at", "programs", ["deleted_at"])
    op.create_table(
        "program_translations", *base_columns(),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False), sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=True), sa.Column("description", sa.Text(), nullable=True),
        sa.Column("career_opportunities", sa.Text(), nullable=True), sa.Column("admissions_info", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["language_id"], ["languages.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("program_id", "language_id", name="uq_program_language"),
        sa.UniqueConstraint("language_id", "slug", name="uq_program_language_slug")
    )
    op.create_index("ix_program_translations_program_id", "program_translations", ["program_id"])
    op.create_index("ix_program_translations_language_id", "program_translations", ["language_id"])

    op.create_table(
        "department_galleries", *base_columns(),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cover_object_key", sa.String(512), nullable=True), sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False), sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_department_galleries_department_id", "department_galleries", ["department_id"])
    op.create_index("ix_department_galleries_is_active", "department_galleries", ["is_active"])
    op.create_index("ix_department_galleries_deleted_at", "department_galleries", ["deleted_at"])
    op.create_table(
        "department_gallery_translations", *base_columns(),
        sa.Column("gallery_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("language_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["gallery_id"], ["department_galleries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["language_id"], ["languages.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gallery_id", "language_id", name="uq_department_gallery_language")
    )
    op.create_index("ix_department_gallery_translations_gallery_id", "department_gallery_translations", ["gallery_id"])
    op.create_index("ix_department_gallery_translations_language_id", "department_gallery_translations", ["language_id"])
    op.create_table(
        "department_gallery_items", *base_columns(),
        sa.Column("gallery_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("media_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("caption", sa.String(500), nullable=True), sa.Column("alt_text", sa.String(255), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False), sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(["gallery_id"], ["department_galleries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_item_id"], ["media_items.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_department_gallery_items_gallery_id", "department_gallery_items", ["gallery_id"])
    op.create_index("ix_department_gallery_items_media_item_id", "department_gallery_items", ["media_item_id"])

    op.add_column("articles", sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("articles", sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("articles", sa.Column("article_type", sa.String(30), server_default="news", nullable=False))
    op.create_foreign_key("fk_articles_department_id", "articles", "departments", ["department_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_articles_program_id", "articles", "programs", ["program_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_articles_department_id", "articles", ["department_id"])
    op.create_index("ix_articles_program_id", "articles", ["program_id"])
    op.create_index("ix_articles_article_type", "articles", ["article_type"])


def downgrade() -> None:
    for index in ("ix_articles_article_type", "ix_articles_program_id", "ix_articles_department_id"):
        op.drop_index(index, table_name="articles")
    op.drop_constraint("fk_articles_program_id", "articles", type_="foreignkey")
    op.drop_constraint("fk_articles_department_id", "articles", type_="foreignkey")
    op.drop_column("articles", "article_type")
    op.drop_column("articles", "program_id")
    op.drop_column("articles", "department_id")
    op.drop_table("department_gallery_items")
    op.drop_table("department_gallery_translations")
    op.drop_table("department_galleries")
    op.drop_table("program_translations")
    op.drop_table("programs")
