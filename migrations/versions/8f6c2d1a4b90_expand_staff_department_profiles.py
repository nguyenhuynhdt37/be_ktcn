"""expand staff and department profiles

Revision ID: 8f6c2d1a4b90
Revises: 38171cc369dc
Create Date: 2026-07-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f6c2d1a4b90"
down_revision: Union[str, None] = "38171cc369dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("staffs", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("staffs", sa.Column("gender", sa.String(length=20), nullable=True))
    op.add_column("staffs", sa.Column("normalized_full_name", sa.String(length=255), nullable=True))
    op.add_column(
        "staffs",
        sa.Column("profile_status", sa.String(length=30), server_default="imported", nullable=False),
    )
    op.add_column(
        "staffs",
        sa.Column("is_visible", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("staffs", sa.Column("note", sa.Text(), nullable=True))
    op.add_column("staffs", sa.Column("source_type", sa.String(length=50), nullable=True))
    op.add_column("staffs", sa.Column("source_note", sa.Text(), nullable=True))
    op.add_column("staffs", sa.Column("source_file_id", sa.UUID(), nullable=True))
    op.execute(
        "UPDATE staffs SET profile_status = 'completed', is_visible = is_active "
        "WHERE deleted_at IS NULL"
    )
    op.create_check_constraint(
        "ck_staff_profile_status",
        "staffs",
        "profile_status IN ('imported', 'pending_review', 'completed', 'published')",
    )
    op.create_index("idx_staff_profile_status", "staffs", ["profile_status"], unique=False)
    op.create_index("idx_staff_is_visible", "staffs", ["is_visible"], unique=False)
    op.create_index(
        "uidx_staff_identity",
        "staffs",
        ["normalized_full_name", "date_of_birth", "department_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND date_of_birth IS NOT NULL"),
    )

    op.add_column("departments", sa.Column("code", sa.String(length=50), nullable=True))
    op.add_column(
        "departments",
        sa.Column("unit_type", sa.String(length=30), server_default="department", nullable=False),
    )
    op.add_column("departments", sa.Column("parent_id", sa.UUID(), nullable=True))
    op.add_column(
        "departments",
        sa.Column("content_status", sa.String(length=30), server_default="draft", nullable=False),
    )
    op.create_foreign_key(
        "fk_departments_parent_id", "departments", "departments", ["parent_id"], ["id"], ondelete="SET NULL"
    )
    op.create_check_constraint(
        "ck_department_unit_type",
        "departments",
        "unit_type IN ('school', 'faculty', 'department', 'office', 'center', 'lab')",
    )
    op.create_check_constraint(
        "ck_department_content_status",
        "departments",
        "content_status IN ('draft', 'review', 'published')",
    )
    op.create_index(
        "uidx_department_code",
        "departments",
        ["code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND code IS NOT NULL"),
    )
    op.create_index("idx_department_unit_type", "departments", ["unit_type"], unique=False)
    op.create_index("idx_department_parent_id", "departments", ["parent_id"], unique=False)

    op.add_column("department_translations", sa.Column("short_description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("department_translations", "short_description")

    op.drop_index("idx_department_parent_id", table_name="departments")
    op.drop_index("idx_department_unit_type", table_name="departments")
    op.drop_index("uidx_department_code", table_name="departments", postgresql_where=sa.text("deleted_at IS NULL AND code IS NOT NULL"))
    op.drop_constraint("ck_department_content_status", "departments", type_="check")
    op.drop_constraint("ck_department_unit_type", "departments", type_="check")
    op.drop_constraint("fk_departments_parent_id", "departments", type_="foreignkey")
    op.drop_column("departments", "content_status")
    op.drop_column("departments", "parent_id")
    op.drop_column("departments", "unit_type")
    op.drop_column("departments", "code")

    op.drop_index("uidx_staff_identity", table_name="staffs", postgresql_where=sa.text("deleted_at IS NULL AND date_of_birth IS NOT NULL"))
    op.drop_index("idx_staff_is_visible", table_name="staffs")
    op.drop_index("idx_staff_profile_status", table_name="staffs")
    op.drop_constraint("ck_staff_profile_status", "staffs", type_="check")
    op.drop_column("staffs", "source_file_id")
    op.drop_column("staffs", "source_note")
    op.drop_column("staffs", "source_type")
    op.drop_column("staffs", "note")
    op.drop_column("staffs", "is_visible")
    op.drop_column("staffs", "profile_status")
    op.drop_column("staffs", "normalized_full_name")
    op.drop_column("staffs", "gender")
    op.drop_column("staffs", "date_of_birth")
