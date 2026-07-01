"""add_menu_item_translations

Revision ID: 46c084449deb
Revises: a54da999ea87
Create Date: 2026-07-01 11:44:05.150891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46c084449deb'
down_revision: Union[str, None] = 'a54da999ea87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tạo bảng menu_item_translations
    op.create_table(
        'menu_item_translations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('menu_item_id', sa.UUID(), nullable=False),
        sa.Column('language_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('menu_item_id', 'language_id', name='uq_menu_item_language_unique')
    )

    # 2. Đồng bộ dữ liệu title cũ sang menu_item_translations dưới dạng ngôn ngữ 'vi'
    connection = op.get_bind()
    lang_row = connection.execute(
        sa.text("SELECT id FROM languages WHERE code = 'vi'")
    ).fetchone()

    if lang_row:
        vi_lang_id = lang_row[0]
        # Lấy tất cả menu items cũ có title
        menu_items = connection.execute(
            sa.text("SELECT id, title FROM menu_items WHERE title IS NOT NULL")
        ).fetchall()

        # Di chuyển dữ liệu sang bảng dịch
        for item_id, title in menu_items:
            import uuid
            trans_id = str(uuid.uuid4())
            connection.execute(
                sa.text("""
                    INSERT INTO menu_item_translations (id, menu_item_id, language_id, title, created_at, updated_at)
                    VALUES (:id, :menu_item_id, :language_id, :title, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """),
                {"id": trans_id, "menu_item_id": str(item_id), "language_id": str(vi_lang_id), "title": title}
            )

    # 3. Xóa cột title khỏi bảng menu_items
    op.drop_column('menu_items', 'title')


def downgrade() -> None:
    # 1. Thêm lại cột title vào menu_items (cho phép nullable để thực hiện di chuyển dữ liệu)
    op.add_column('menu_items', sa.Column('title', sa.String(length=255), nullable=True))

    # 2. Phục hồi dữ liệu title tiếng Việt ngược lại menu_items
    connection = op.get_bind()
    lang_row = connection.execute(
        sa.text("SELECT id FROM languages WHERE code = 'vi'")
    ).fetchone()

    if lang_row:
        vi_lang_id = lang_row[0]
        translations = connection.execute(
            sa.text("SELECT menu_item_id, title FROM menu_item_translations WHERE language_id = :lang_id"),
            {"lang_id": str(vi_lang_id)}
        ).fetchall()

        for menu_item_id, title in translations:
            connection.execute(
                sa.text("UPDATE menu_items SET title = :title WHERE id = :menu_item_id"),
                {"title": title, "menu_item_id": str(menu_item_id)}
            )

    # Đặt lại cột title thành NOT NULL sau khi đã khôi phục dữ liệu
    op.alter_column('menu_items', 'title', nullable=False)

    # 3. Xóa bảng menu_item_translations
    op.drop_table('menu_item_translations')
