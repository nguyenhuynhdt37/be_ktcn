"""move_external_url_to_translations

Revision ID: d484c2dee627
Revises: fbf2c440aade
Create Date: 2026-07-12 11:18:31.036826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd484c2dee627'
down_revision: Union[str, None] = 'fbf2c440aade'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Thêm cột external_url vào bảng menu_item_translations
    op.add_column('menu_item_translations', sa.Column('external_url', sa.String(length=500), nullable=True))
    
    # 2. Di chuyển dữ liệu external_url cũ từ menu_items sang các bản dịch tương ứng
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE menu_item_translations
            SET external_url = menu_items.external_url
            FROM menu_items
            WHERE menu_item_translations.menu_item_id = menu_items.id
            AND menu_items.external_url IS NOT NULL
            """
        )
    )

    # 3. Drop check constraint cũ vì nó tham chiếu tới menu_items.external_url
    op.drop_constraint('chk_menu_items_target_consistency', 'menu_items', type_='check')

    # 4. Xóa cột external_url khỏi bảng menu_items
    op.drop_column('menu_items', 'external_url')

    # 5. Tạo check constraint mới không tham chiếu tới external_url
    op.create_check_constraint(
        'chk_menu_items_target_consistency',
        'menu_items',
        """
        (target_type = 'EXTERNAL_LINK' AND target_id IS NULL)
        OR (target_type IS NOT NULL AND target_type != 'EXTERNAL_LINK' AND target_id IS NOT NULL)
        OR (target_type IS NULL AND target_id IS NULL)
        """
    )


def downgrade() -> None:
    # 1. Thêm cột external_url trở lại bảng menu_items
    op.add_column('menu_items', sa.Column('external_url', sa.String(length=500), nullable=True))

    # 2. Di chuyển dữ liệu external_url ngược lại từ bản dịch sang menu_items
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE menu_items
            SET external_url = menu_item_translations.external_url
            FROM menu_item_translations
            WHERE menu_items.id = menu_item_translations.menu_item_id
            AND menu_item_translations.external_url IS NOT NULL
            """
        )
    )

    # 3. Drop check constraint mới
    op.drop_constraint('chk_menu_items_target_consistency', 'menu_items', type_='check')

    # 4. Xóa cột external_url khỏi bảng menu_item_translations
    op.drop_column('menu_item_translations', 'external_url')

    # 5. Tạo check constraint cũ
    op.create_check_constraint(
        'chk_menu_items_target_consistency',
        'menu_items',
        """
        (target_type = 'EXTERNAL_LINK' AND external_url IS NOT NULL AND target_id IS NULL)
        OR (target_type IS NOT NULL AND target_type != 'EXTERNAL_LINK' AND target_id IS NOT NULL AND external_url IS NULL)
        OR (target_type IS NULL AND target_id IS NULL AND external_url IS NULL)
        """
    )
