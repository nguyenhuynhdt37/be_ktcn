"""add_ai_budget_pricing_and_logs

Revision ID: 7fa886554bd9
Revises: 9076ce5fdb85
Create Date: 2026-06-27 22:23:41.393241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fa886554bd9'
down_revision: Union[str, None] = '9076ce5fdb85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ai_model_pricing table
    op.create_table('ai_model_pricing',
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('model_name', sa.String(length=100), nullable=False),
    sa.Column('input_price_per_1m', sa.Numeric(precision=10, scale=4), nullable=False),
    sa.Column('output_price_per_1m', sa.Numeric(precision=10, scale=4), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_model_pricing_model_name'), 'ai_model_pricing', ['model_name'], unique=True)
    op.create_index(op.f('ix_ai_model_pricing_provider'), 'ai_model_pricing', ['provider'], unique=False)
    
    # Create ai_usage_logs table
    op.create_table('ai_usage_logs',
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('model', sa.String(length=100), nullable=False),
    sa.Column('feature', sa.String(length=50), nullable=False),
    sa.Column('prompt_tokens', sa.Integer(), nullable=False),
    sa.Column('completion_tokens', sa.Integer(), nullable=False),
    sa.Column('total_tokens', sa.Integer(), nullable=False),
    sa.Column('cost', sa.Numeric(precision=12, scale=6), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_usage_logs_user_id'), 'ai_usage_logs', ['user_id'], unique=False)
    
    # Add columns to ai_settings table
    op.add_column('ai_settings', sa.Column('monthly_budget_limit', sa.Numeric(precision=10, scale=4), nullable=False, server_default='50.0000'))
    op.add_column('ai_settings', sa.Column('monthly_spent', sa.Numeric(precision=10, scale=4), nullable=False, server_default='0.0000'))
    op.add_column('ai_settings', sa.Column('budget_reset_day', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('ai_settings', sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'))


def downgrade() -> None:
    op.drop_column('ai_settings', 'currency')
    op.drop_column('ai_settings', 'budget_reset_day')
    op.drop_column('ai_settings', 'monthly_spent')
    op.drop_column('ai_settings', 'monthly_budget_limit')
    op.drop_index(op.f('ix_ai_usage_logs_user_id'), table_name='ai_usage_logs')
    op.drop_table('ai_usage_logs')
    op.drop_index(op.f('ix_ai_model_pricing_provider'), table_name='ai_model_pricing')
    op.drop_index(op.f('ix_ai_model_pricing_model_name'), table_name='ai_model_pricing')
    op.drop_table('ai_model_pricing')
