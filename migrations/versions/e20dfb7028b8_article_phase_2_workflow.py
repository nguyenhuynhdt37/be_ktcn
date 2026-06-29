"""article_phase_2_workflow

Revision ID: e20dfb7028b8
Revises: 83dc3707cde2
Create Date: 2026-06-28 23:25:15.847995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e20dfb7028b8'
down_revision: Union[str, None] = '83dc3707cde2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add REJECTED to article_status_enum (Postgres only)
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute("ALTER TYPE article_status_enum ADD VALUE IF NOT EXISTS 'REJECTED'")

    # 2. Workflow logs setup
    op.execute("DROP TABLE IF EXISTS article_workflow_logs")
    
    op.create_table('article_workflow_logs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('article_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.Enum('SUBMIT', 'RESUBMIT', 'APPROVE', 'REJECT', 'PUBLISH', 'SCHEDULE', 'CANCEL_SCHEDULE', 'UNPUBLISH', 'ARCHIVE', name='workflow_action_enum'), nullable=False),
        sa.Column('from_status', postgresql.ENUM('DRAFT', 'PENDING', 'REJECTED', 'PUBLISHED', 'ARCHIVED', name='article_status_enum', create_type=False), nullable=True),
        sa.Column('to_status', postgresql.ENUM('DRAFT', 'PENDING', 'REJECTED', 'PUBLISHED', 'ARCHIVED', name='article_status_enum', create_type=False), nullable=True),
        sa.Column('action_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['action_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_article_workflow_logs_action'), 'article_workflow_logs', ['action'], unique=False)
    op.create_index(op.f('ix_article_workflow_logs_action_by'), 'article_workflow_logs', ['action_by'], unique=False)
    op.create_index(op.f('ix_article_workflow_logs_article_id'), 'article_workflow_logs', ['article_id'], unique=False)

    # 3. Add columns to articles
    op.add_column('articles', sa.Column('approved_by', sa.UUID(), nullable=True))
    op.add_column('articles', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('published_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('articles', sa.Column('scheduled_publish_at', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(None, 'articles', 'users', ['approved_by'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # Revert articles table changes
    op.drop_constraint(None, 'articles', type_='foreignkey')
    op.drop_column('articles', 'scheduled_publish_at')
    op.drop_column('articles', 'published_at')
    op.drop_column('articles', 'rejection_reason')
    op.drop_column('articles', 'approved_by')
    
    # Drop workflow logs
    op.drop_table('article_workflow_logs')
    op.execute("DROP TYPE IF EXISTS workflow_action_enum")
