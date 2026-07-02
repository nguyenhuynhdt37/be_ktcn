"""ensure_translation_cascade_delete

Revision ID: 0dc542f085e0
Revises: 767c77b1f001
Create Date: 2026-07-01 18:03:57.926197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0dc542f085e0'
down_revision: Union[str, None] = '767c77b1f001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    
    # Danh sách các bảng dịch, bảng cha tương ứng, và cột khóa ngoại
    tables_info = [
        ("academic_title_translations", "academic_titles", "academic_title_id"),
        ("degree_translations", "degrees", "degree_id"),
        ("department_translations", "departments", "department_id"),
        ("position_translations", "positions", "position_id"),
        ("staff_translations", "staffs", "staff_id"),
        ("category_translations", "categories", "category_id"),
        ("menu_item_translations", "menu_items", "menu_item_id")
    ]
    
    for child_table, parent_table, fk_col in tables_info:
        # Truy vấn tìm tên constraint thực tế của foreign key từ child_table sang parent_table
        query = sa.text(f"""
            SELECT con.conname 
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            WHERE rel.relname = '{child_table}'
              AND con.contype = 'f'
              AND con.confrelid = '{parent_table}'::regclass;
        """)
        
        result = connection.execute(query).fetchall()
        for row in result:
            con_name = row[0]
            # Drop constraint cũ
            op.drop_constraint(con_name, child_table, type_='foreignkey')
            # Tạo constraint mới với ondelete='CASCADE'
            op.create_foreign_key(
                con_name, 
                child_table, 
                parent_table, 
                [fk_col], 
                ['id'], 
                ondelete='CASCADE'
            )


def downgrade() -> None:
    # Downgrade sẽ khôi phục lại các foreign key constraint cũ (mặc định RESTRICT hoặc CASCADE tùy theo model hiện tại)
    # Tuy nhiên vì dự án hiện tại hướng tới CASCADE nên chúng ta giữ nguyên.
    pass
