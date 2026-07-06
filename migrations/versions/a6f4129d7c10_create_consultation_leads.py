"""create consultation leads

Revision ID: a6f4129d7c10
Revises: 88cecd01e508
Create Date: 2026-07-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a6f4129d7c10"
down_revision: str | None = "88cecd01e508"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


consultation_request_type = postgresql.ENUM(
    "ADMISSION_CONSULTING",
    "CAMPUS_VISIT",
    "RECEIVE_MATERIALS",
    "APPLICATION_REGISTRATION",
    name="consultation_request_type",
    create_type=False,
)
consultation_status = postgresql.ENUM(
    "NEW",
    "CONTACTED",
    "CONSULTING",
    "COMPLETED",
    "NOT_QUALIFIED",
    name="consultation_status",
    create_type=False,
)


def upgrade() -> None:
    consultation_request_type.create(op.get_bind(), checkfirst=True)
    consultation_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "consultation_leads",
        sa.Column("reference_code", sa.String(length=20), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("interested_major", sa.String(length=255), nullable=False),
        sa.Column("request_type", consultation_request_type, nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("consent_given", sa.Boolean(), nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("status", consultation_status, nullable=False),
        sa.Column("assigned_to_id", sa.UUID(), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference_code"),
    )
    op.create_index(
        "idx_consultation_leads_created_at",
        "consultation_leads",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "idx_consultation_leads_phone_created",
        "consultation_leads",
        ["phone", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_consultation_leads_status_created",
        "consultation_leads",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consultation_leads_assigned_to_id"),
        "consultation_leads",
        ["assigned_to_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consultation_leads_email"),
        "consultation_leads",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consultation_leads_phone"),
        "consultation_leads",
        ["phone"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consultation_leads_status"),
        "consultation_leads",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_consultation_leads_status"), table_name="consultation_leads")
    op.drop_index(op.f("ix_consultation_leads_phone"), table_name="consultation_leads")
    op.drop_index(op.f("ix_consultation_leads_email"), table_name="consultation_leads")
    op.drop_index(
        op.f("ix_consultation_leads_assigned_to_id"),
        table_name="consultation_leads",
    )
    op.drop_index(
        "idx_consultation_leads_status_created", table_name="consultation_leads"
    )
    op.drop_index(
        "idx_consultation_leads_phone_created", table_name="consultation_leads"
    )
    op.drop_index("idx_consultation_leads_created_at", table_name="consultation_leads")
    op.drop_table("consultation_leads")
    consultation_status.drop(op.get_bind(), checkfirst=True)
    consultation_request_type.drop(op.get_bind(), checkfirst=True)
