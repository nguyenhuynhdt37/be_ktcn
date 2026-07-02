"""add_academic_title_and_degree

Revision ID: 767c77b1f001
Revises: 3e27c966b3cf
Create Date: 2026-07-01 14:56:05.859114

"""
from typing import Sequence, Union
import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '767c77b1f001'
down_revision: Union[str, None] = '3e27c966b3cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tạo bảng academic_titles
    op.create_table(
        'academic_titles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_academic_titles_deleted_at'), 'academic_titles', ['deleted_at'], unique=False)

    # 2. Tạo bảng academic_title_translations
    op.create_table(
        'academic_title_translations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('academic_title_id', sa.UUID(), nullable=False),
        sa.Column('language_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('abbreviation', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['academic_title_id'], ['academic_titles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('academic_title_id', 'language_id', name='uq_academic_title_language_unique')
    )

    # 3. Tạo bảng degrees
    op.create_table(
        'degrees',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_degrees_deleted_at'), 'degrees', ['deleted_at'], unique=False)

    # 4. Tạo bảng degree_translations
    op.create_table(
        'degree_translations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('degree_id', sa.UUID(), nullable=False),
        sa.Column('language_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('abbreviation', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['degree_id'], ['degrees.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('degree_id', 'language_id', name='uq_degree_language_unique')
    )

    # 5. Thêm cột khóa ngoại vào staffs
    op.add_column('staffs', sa.Column('academic_title_id', sa.UUID(), nullable=True))
    op.add_column('staffs', sa.Column('degree_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_staffs_academic_title_id', 'staffs', 'academic_titles', ['academic_title_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_staffs_degree_id', 'staffs', 'degrees', ['degree_id'], ['id'], ondelete='SET NULL')

    # 6. Seed dữ liệu mặc định & Di trú dữ liệu cũ
    connection = op.get_bind()
    
    # Lấy language IDs
    langs_res = connection.execute(sa.text("SELECT id, code FROM languages;"))
    lang_map = {row[1]: row[0] for row in langs_res.all()}
    vi_id = lang_map.get('vi')
    en_id = lang_map.get('en')

    # Fallback tạo languages nếu không tồn tại (chủ yếu trong môi trường test sạch)
    if not vi_id:
        vi_id = uuid.uuid4()
        connection.execute(sa.text(
            f"INSERT INTO languages (id, code, name, native_name, is_default, is_system, is_active, sort_order, created_at, updated_at) "
            f"VALUES ('{vi_id}', 'vi', 'Vietnamese', 'Tiếng Việt', true, true, true, 1, now(), now());"
        ))
    if not en_id:
        en_id = uuid.uuid4()
        connection.execute(sa.text(
            f"INSERT INTO languages (id, code, name, native_name, is_default, is_system, is_active, sort_order, created_at, updated_at) "
            f"VALUES ('{en_id}', 'en', 'English', 'English', false, true, true, 2, now(), now());"
        ))

    # A. Seed Học hàm (Academic Titles)
    titles_data = [
        {
            "id": uuid.uuid4(),
            "sort_order": 1,
            "translations": {
                "vi": {"name": "Giáo sư", "abbr": "GS"},
                "en": {"name": "Professor", "abbr": "Prof."}
            }
        },
        {
            "id": uuid.uuid4(),
            "sort_order": 2,
            "translations": {
                "vi": {"name": "Phó giáo sư", "abbr": "PGS"},
                "en": {"name": "Associate Professor", "abbr": "Assoc. Prof."}
            }
        }
    ]
    for t in titles_data:
        connection.execute(sa.text(
            f"INSERT INTO academic_titles (id, sort_order, is_active, created_at, updated_at) "
            f"VALUES ('{t['id']}', {t['sort_order']}, true, now(), now());"
        ))
        # Bản dịch vi
        connection.execute(sa.text(
            f"INSERT INTO academic_title_translations (id, academic_title_id, language_id, name, abbreviation, created_at, updated_at) "
            f"VALUES ('{uuid.uuid4()}', '{t['id']}', '{vi_id}', '{t['translations']['vi']['name']}', '{t['translations']['vi']['abbr']}', now(), now());"
        ))
        # Bản dịch en
        connection.execute(sa.text(
            f"INSERT INTO academic_title_translations (id, academic_title_id, language_id, name, abbreviation, created_at, updated_at) "
            f"VALUES ('{uuid.uuid4()}', '{t['id']}', '{en_id}', '{t['translations']['en']['name']}', '{t['translations']['en']['abbr']}', now(), now());"
        ))

    # B. Seed Học vị (Degrees)
    degrees_data = [
        {
            "id": uuid.uuid4(),
            "sort_order": 1,
            "translations": {
                "vi": {"name": "Tiến sĩ khoa học", "abbr": "TSKH"},
                "en": {"name": "Doctor of Science", "abbr": "D.Sc."}
            }
        },
        {
            "id": uuid.uuid4(),
            "sort_order": 2,
            "translations": {
                "vi": {"name": "Tiến sĩ", "abbr": "TS"},
                "en": {"name": "Doctor of Philosophy", "abbr": "Ph.D."}
            }
        },
        {
            "id": uuid.uuid4(),
            "sort_order": 3,
            "translations": {
                "vi": {"name": "Thạc sĩ", "abbr": "ThS"},
                "en": {"name": "Master of Science", "abbr": "M.Sc."}
            }
        },
        {
            "id": uuid.uuid4(),
            "sort_order": 4,
            "translations": {
                "vi": {"name": "Cử nhân", "abbr": "CN"},
                "en": {"name": "Bachelor", "abbr": "B.S."}
            }
        },
        {
            "id": uuid.uuid4(),
            "sort_order": 5,
            "translations": {
                "vi": {"name": "Kỹ sư", "abbr": "KS"},
                "en": {"name": "Engineer", "abbr": "Eng."}
            }
        },
        {
            "id": uuid.uuid4(),
            "sort_order": 6,
            "translations": {
                "vi": {"name": "Bác sĩ", "abbr": "BS"},
                "en": {"name": "Doctor of Medicine", "abbr": "MD"}
            }
        }
    ]
    for d in degrees_data:
        connection.execute(sa.text(
            f"INSERT INTO degrees (id, sort_order, is_active, created_at, updated_at) "
            f"VALUES ('{d['id']}', {d['sort_order']}, true, now(), now());"
        ))
        # Bản dịch vi
        connection.execute(sa.text(
            f"INSERT INTO degree_translations (id, degree_id, language_id, name, abbreviation, created_at, updated_at) "
            f"VALUES ('{uuid.uuid4()}', '{d['id']}', '{vi_id}', '{d['translations']['vi']['name']}', '{d['translations']['vi']['abbr']}', now(), now());"
        ))
        # Bản dịch en
        connection.execute(sa.text(
            f"INSERT INTO degree_translations (id, degree_id, language_id, name, abbreviation, created_at, updated_at) "
            f"VALUES ('{uuid.uuid4()}', '{d['id']}', '{en_id}', '{d['translations']['en']['name']}', '{d['translations']['en']['abbr']}', now(), now());"
        ))

    # C. Di trú dữ liệu cũ: Đọc từ staff_translations để map sang staffs
    staff_trans_res = connection.execute(sa.text(
        "SELECT staff_id, academic_title, degree FROM staff_translations;"
    ))
    
    # Bản đồ map text để khớp học hàm & học vị
    # GS (Giáo sư) / PGS (Phó giáo sư)
    gs_id = titles_data[0]["id"]
    pgs_id = titles_data[1]["id"]
    
    # Học vị
    tskh_id = degrees_data[0]["id"]
    ts_id = degrees_data[1]["id"]
    ths_id = degrees_data[2]["id"]
    cn_id = degrees_data[3]["id"]
    ks_id = degrees_data[4]["id"]
    bs_id = degrees_data[5]["id"]

    for row in staff_trans_res.all():
        s_id = row[0]
        title_text = row[1]
        degree_text = row[2]

        selected_title_id = "NULL"
        if title_text:
            title_text_lower = title_text.lower()
            if "phó giáo sư" in title_text_lower or "pgs" in title_text_lower or "associate" in title_text_lower:
                selected_title_id = f"'{pgs_id}'"
            elif "giáo sư" in title_text_lower or "gs" in title_text_lower or "professor" in title_text_lower:
                selected_title_id = f"'{gs_id}'"

        selected_degree_id = "NULL"
        if degree_text:
            deg_text_lower = degree_text.lower()
            if "tiến sĩ khoa học" in deg_text_lower or "tskh" in deg_text_lower or "science" in deg_text_lower:
                selected_degree_id = f"'{tskh_id}'"
            elif "tiến sĩ" in deg_text_lower or "ts" in deg_text_lower or "ph.d" in deg_text_lower or "phd" in deg_text_lower or "doctor" in deg_text_lower:
                selected_degree_id = f"'{ts_id}'"
            elif "thạc sĩ" in deg_text_lower or "ths" in deg_text_lower or "master" in deg_text_lower:
                selected_degree_id = f"'{ths_id}'"
            elif "kỹ sư" in deg_text_lower or "ks" in deg_text_lower or "engineer" in deg_text_lower:
                selected_degree_id = f"'{ks_id}'"
            elif "bác sĩ" in deg_text_lower or "bs" in deg_text_lower or "medicine" in deg_text_lower:
                selected_degree_id = f"'{bs_id}'"
            elif "cử nhân" in deg_text_lower or "cn" in deg_text_lower or "bachelor" in deg_text_lower:
                selected_degree_id = f"'{cn_id}'"

        if selected_title_id != "NULL" or selected_degree_id != "NULL":
            updates = []
            if selected_title_id != "NULL":
                updates.append(f"academic_title_id = {selected_title_id}")
            if selected_degree_id != "NULL":
                updates.append(f"degree_id = {selected_degree_id}")
            
            connection.execute(sa.text(
                f"UPDATE staffs SET {', '.join(updates)} WHERE id = '{s_id}';"
            ))

    # D. Xóa hai cột cũ khỏi staff_translations
    op.drop_column('staff_translations', 'academic_title')
    op.drop_column('staff_translations', 'degree')


def downgrade() -> None:
    # Thêm lại hai cột vào staff_translations
    op.add_column('staff_translations', sa.Column('academic_title', sa.String(length=50), nullable=True))
    op.add_column('staff_translations', sa.Column('degree', sa.String(length=100), nullable=True))

    # Xóa cột khóa ngoại khỏi staffs
    op.drop_constraint('fk_staffs_degree_id', 'staffs', type_='foreignkey')
    op.drop_constraint('fk_staffs_academic_title_id', 'staffs', type_='foreignkey')
    op.drop_column('staffs', 'degree_id')
    op.drop_column('staffs', 'academic_title_id')

    # Xóa các bảng
    op.drop_table('degree_translations')
    op.drop_index(op.f('ix_degrees_deleted_at'), table_name='degrees')
    op.drop_table('degrees')
    op.drop_table('academic_title_translations')
    op.drop_index(op.f('ix_academic_titles_deleted_at'), table_name='academic_titles')
    op.drop_table('academic_titles')
