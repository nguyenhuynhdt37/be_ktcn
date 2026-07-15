"""add program academic profile

Revision ID: a12f4c8e9d31
Revises: 9f1852b322bf
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a12f4c8e9d31"
down_revision: str | None = "9f1852b322bf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def base_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "program_versions",
        *base_columns(),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_year", sa.Integer(), nullable=False),
        sa.Column("cohort_code", sa.String(50), nullable=True),
        sa.Column("total_credits", sa.Numeric(6, 1), nullable=True),
        sa.Column(
            "is_current", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column(
            "is_published", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "program_id", "version_year", name="uq_program_version_year"
        ),
    )
    op.create_index(
        "ix_program_versions_program_id", "program_versions", ["program_id"]
    )
    op.create_index(
        "ix_program_versions_is_current", "program_versions", ["is_current"]
    )
    op.create_index(
        "ix_program_versions_is_published", "program_versions", ["is_published"]
    )

    op.create_table(
        "program_version_translations",
        *base_columns(),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("general_objective", sa.Text(), nullable=True),
        sa.Column("career_opportunities", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["version_id"], ["program_versions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["language_id"], ["languages.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "version_id", "language_id", name="uq_program_version_language"
        ),
    )
    op.create_index(
        "ix_program_version_translations_version_id",
        "program_version_translations",
        ["version_id"],
    )
    op.create_index(
        "ix_program_version_translations_language_id",
        "program_version_translations",
        ["language_id"],
    )

    op.create_table(
        "program_documents",
        *base_columns(),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "document_type", sa.String(50), server_default="other", nullable=False
        ),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("object_key", sa.String(512), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(
            ["version_id"], ["program_versions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_program_documents_version_id", "program_documents", ["version_id"]
    )

    op.create_table(
        "program_document_translations",
        *base_columns(),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"], ["program_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["language_id"], ["languages.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id", "language_id", name="uq_program_document_language"
        ),
    )
    op.create_index(
        "ix_program_document_translations_document_id",
        "program_document_translations",
        ["document_id"],
    )
    op.create_index(
        "ix_program_document_translations_language_id",
        "program_document_translations",
        ["language_id"],
    )

    op.create_table(
        "program_outcomes",
        *base_columns(),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("outcome_type", sa.String(30), nullable=False),
        sa.Column("parent_code", sa.String(30), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(
            ["version_id"], ["program_versions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "version_id", "code", "outcome_type", name="uq_program_outcome_code"
        ),
    )
    op.create_index(
        "ix_program_outcomes_version_id", "program_outcomes", ["version_id"]
    )

    op.create_table(
        "program_outcome_translations",
        *base_columns(),
        sa.Column("outcome_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["outcome_id"], ["program_outcomes.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["language_id"], ["languages.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "outcome_id", "language_id", name="uq_program_outcome_language"
        ),
    )
    op.create_index(
        "ix_program_outcome_translations_outcome_id",
        "program_outcome_translations",
        ["outcome_id"],
    )
    op.create_index(
        "ix_program_outcome_translations_language_id",
        "program_outcome_translations",
        ["language_id"],
    )

    op.create_table(
        "program_courses",
        *base_columns(),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_code", sa.String(50), nullable=True),
        sa.Column("row_type", sa.String(30), server_default="course", nullable=False),
        sa.Column("credits", sa.Numeric(5, 1), nullable=True),
        sa.Column("credits_text", sa.String(30), nullable=True),
        sa.Column("semester", sa.String(30), nullable=True),
        sa.Column("knowledge_block", sa.String(100), nullable=True),
        sa.Column("course_type", sa.String(50), nullable=True),
        sa.Column("managing_unit", sa.String(255), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(
            ["version_id"], ["program_versions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version_id", "course_code", name="uq_program_course_code"),
    )
    op.create_index("ix_program_courses_version_id", "program_courses", ["version_id"])

    op.create_table(
        "program_course_translations",
        *base_columns(),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["program_courses.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["language_id"], ["languages.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "course_id", "language_id", name="uq_program_course_language"
        ),
    )
    op.create_index(
        "ix_program_course_translations_course_id",
        "program_course_translations",
        ["course_id"],
    )
    op.create_index(
        "ix_program_course_translations_language_id",
        "program_course_translations",
        ["language_id"],
    )


def downgrade() -> None:
    for table in (
        "program_course_translations",
        "program_courses",
        "program_outcome_translations",
        "program_outcomes",
        "program_document_translations",
        "program_documents",
        "program_version_translations",
        "program_versions",
    ):
        op.drop_table(table)
