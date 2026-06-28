"""add_menus_and_menu_items

Revision ID: 9ad1a1e34447
Revises: 
Create Date: 2026-06-27 20:14:12.912090

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ad1a1e34447'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create menus table
    op.create_table('menus',
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )

    # Create menu_items table with CHECK constraints
    op.create_table('menu_items',
    sa.Column('menu_id', sa.UUID(), nullable=False),
    sa.Column('parent_id', sa.UUID(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('target_type', sa.Enum('CATEGORY', 'ARTICLE', 'PAGE', 'MODULE', 'EXTERNAL_LINK', name='menu_item_target_type', native_enum=False), nullable=True),
    sa.Column('target_id', sa.Uuid(), nullable=True),
    sa.Column('external_url', sa.String(length=500), nullable=True),
    sa.Column('open_in_new_tab', sa.Boolean(), nullable=False),
    sa.Column('icon', sa.String(length=100), nullable=True),
    sa.Column('depth', sa.Integer(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('is_visible', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint(
        "(target_type = 'EXTERNAL_LINK' AND external_url IS NOT NULL AND target_id IS NULL) "
        "OR (target_type IS NOT NULL AND target_type != 'EXTERNAL_LINK' AND target_id IS NOT NULL AND external_url IS NULL) "
        "OR (target_type IS NULL AND target_id IS NULL AND external_url IS NULL)",
        name='chk_menu_items_target_consistency',
    ),
    sa.CheckConstraint('depth >= 1 AND depth <= 3', name='chk_menu_items_depth'),
    sa.ForeignKeyConstraint(['menu_id'], ['menus.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_id'], ['menu_items.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_menu_items_menu_id'), 'menu_items', ['menu_id'], unique=False)
    op.create_index(op.f('ix_menu_items_parent_id'), 'menu_items', ['parent_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_menu_items_parent_id'), table_name='menu_items')
    op.drop_index(op.f('ix_menu_items_menu_id'), table_name='menu_items')
    op.drop_table('menu_items')
    op.drop_table('menus')
