"""Add TTS models

Revision ID: 5edd98fd13c3
Revises: e46a2488c90d
Create Date: 2026-06-28 22:20:55.692590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5edd98fd13c3'
down_revision: Union[str, None] = 'e46a2488c90d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tts_voices',
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('voice_code', sa.String(length=50), nullable=False),
    sa.Column('display_name', sa.String(length=100), nullable=False),
    sa.Column('gender', sa.String(length=20), nullable=True),
    sa.Column('region', sa.String(length=50), nullable=True),
    sa.Column('language', sa.String(length=20), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('sample_audio_url', sa.String(length=255), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tts_voices_provider'), 'tts_voices', ['provider'], unique=False)
    op.create_index(op.f('ix_tts_voices_voice_code'), 'tts_voices', ['voice_code'], unique=True)
    
    op.create_table('article_audio',
    sa.Column('article_id', sa.UUID(), nullable=False),
    sa.Column('voice_id', sa.UUID(), nullable=False),
    sa.Column('audio_url', sa.String(length=500), nullable=True),
    sa.Column('word_timestamps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('character_count', sa.Integer(), nullable=True),
    sa.Column('speed', sa.Float(), nullable=True),
    sa.Column('error_message', sa.String(length=500), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['voice_id'], ['tts_voices.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_article_audio_article_id'), 'article_audio', ['article_id'], unique=False)
    op.create_index(op.f('ix_article_audio_status'), 'article_audio', ['status'], unique=False)
    op.create_index(op.f('ix_article_audio_voice_id'), 'article_audio', ['voice_id'], unique=False)

def downgrade() -> None:
    op.drop_table('article_audio')
    op.drop_table('tts_voices')
