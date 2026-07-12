"""add_target_type_to_banners

Revision ID: c51e1026155f
Revises: eafd9139cecc
Create Date: 2026-07-12 13:39:30.390904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c51e1026155f'
down_revision: Union[str, None] = 'eafd9139cecc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Thêm cột target_type là nullable trước để tránh lỗi khi bảng đã có dữ liệu
    op.add_column('banners', sa.Column('target_type', sa.Enum('ARTICLE', 'EXTERNAL', name='banner_target_type', native_enum=False), nullable=True))
    
    # 2. Thực hiện Data Migration cho các bản ghi cũ
    op.execute("UPDATE banners SET target_type = 'ARTICLE' WHERE article_id IS NOT NULL")
    op.execute("UPDATE banners SET target_type = 'EXTERNAL' WHERE article_id IS NULL")
    
    # 3. Thay đổi cột thành NOT NULL
    op.alter_column('banners', 'target_type', nullable=False)
    
    # 4. Thêm check constraint đảm bảo tính nhất quán dữ liệu
    op.create_check_constraint(
        'chk_banner_target_consistency',
        'banners',
        """
        (target_type = 'ARTICLE' AND article_id IS NOT NULL AND link_url IS NULL)
        OR (target_type = 'EXTERNAL' AND article_id IS NULL)
        """
    )


def downgrade() -> None:
    # 1. Xóa Check Constraint
    op.drop_constraint('chk_banner_target_consistency', 'banners', type_='check')
    
    # 2. Xóa cột target_type
    op.drop_column('banners', 'target_type')
