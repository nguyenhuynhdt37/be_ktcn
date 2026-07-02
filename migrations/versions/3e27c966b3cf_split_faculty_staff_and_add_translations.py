"""split_faculty_staff_and_add_translations

Revision ID: 3e27c966b3cf
Revises: 647478ff8670
Create Date: 2026-07-01 12:54:03.347020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e27c966b3cf'
down_revision: Union[str, None] = '647478ff8670'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def slugify(text: str) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text


def upgrade() -> None:
    # 1. Tạo bảng department_translations
    op.create_table(
        'department_translations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('department_id', sa.UUID(), nullable=False),
        sa.Column('language_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('department_id', 'language_id', name='uq_department_language_unique')
    )
    op.create_index('uidx_department_trans_slug', 'department_translations', ['slug'], unique=True)

    # 2. Tạo bảng position_translations
    op.create_table(
        'position_translations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('position_id', sa.UUID(), nullable=False),
        sa.Column('language_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['position_id'], ['positions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('position_id', 'language_id', name='uq_position_language_unique')
    )

    # 3. Tạo bảng staff_translations
    op.create_table(
        'staff_translations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('staff_id', sa.UUID(), nullable=False),
        sa.Column('language_id', sa.UUID(), nullable=False),
        sa.Column('academic_title', sa.String(length=50), nullable=True),
        sa.Column('degree', sa.String(length=100), nullable=True),
        sa.Column('biography', sa.Text(), nullable=True),
        sa.Column('research_interests', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['staff_id'], ['staffs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('staff_id', 'language_id', name='uq_staff_language_unique')
    )

    # 4. Đồng bộ dữ liệu cũ
    connection = op.get_bind()
    vi_lang_id = connection.execute(sa.text("SELECT id FROM languages WHERE code = 'vi'")).scalar()
    en_lang_id = connection.execute(sa.text("SELECT id FROM languages WHERE code = 'en'")).scalar()

    # Đồng bộ Departments
    if vi_lang_id:
        departments = connection.execute(
            sa.text("SELECT id, name, english_name, description, slug FROM departments")
        ).fetchall()

        for dept_id, name, english_name, description, slug in departments:
            import uuid
            vi_trans_id = str(uuid.uuid4())
            connection.execute(
                sa.text("""
                    INSERT INTO department_translations (id, department_id, language_id, name, description, slug, created_at, updated_at)
                    VALUES (:id, :department_id, :language_id, :name, :description, :slug, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """),
                {"id": vi_trans_id, "department_id": str(dept_id), "language_id": str(vi_lang_id), "name": name, "description": description, "slug": slug}
            )

            if en_lang_id and english_name:
                en_trans_id = str(uuid.uuid4())
                en_slug = slugify(english_name)
                existing = connection.execute(
                    sa.text("SELECT 1 FROM department_translations WHERE slug = :slug"),
                    {"slug": en_slug}
                ).scalar()
                if existing:
                    en_slug = f"{en_slug}-{uuid.uuid4().hex[:4]}"
                
                connection.execute(
                    sa.text("""
                        INSERT INTO department_translations (id, department_id, language_id, name, description, slug, created_at, updated_at)
                        VALUES (:id, :department_id, :language_id, :name, :description, :slug, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """),
                    {"id": en_trans_id, "department_id": str(dept_id), "language_id": str(en_lang_id), "name": english_name, "description": description, "slug": en_slug}
                )

    # Đồng bộ Positions
    if vi_lang_id:
        positions = connection.execute(
            sa.text("SELECT id, name, english_name, description FROM positions")
        ).fetchall()

        for pos_id, name, english_name, description in positions:
            import uuid
            vi_trans_id = str(uuid.uuid4())
            connection.execute(
                sa.text("""
                    INSERT INTO position_translations (id, position_id, language_id, name, description, created_at, updated_at)
                    VALUES (:id, :position_id, :language_id, :name, :description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """),
                {"id": vi_trans_id, "position_id": str(pos_id), "language_id": str(vi_lang_id), "name": name, "description": description}
            )

            if en_lang_id and english_name:
                en_trans_id = str(uuid.uuid4())
                connection.execute(
                    sa.text("""
                        INSERT INTO position_translations (id, position_id, language_id, name, description, created_at, updated_at)
                        VALUES (:id, :position_id, :language_id, :name, :description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """),
                    {"id": en_trans_id, "position_id": str(pos_id), "language_id": str(en_lang_id), "name": english_name, "description": description}
                )

    # Đồng bộ Staffs
    if vi_lang_id:
        staffs = connection.execute(
            sa.text("SELECT id, academic_title, degree, biography, research_interests FROM staffs")
        ).fetchall()

        for s_id, academic_title, degree, biography, research_interests in staffs:
            import uuid
            vi_trans_id = str(uuid.uuid4())
            connection.execute(
                sa.text("""
                    INSERT INTO staff_translations (id, staff_id, language_id, academic_title, degree, biography, research_interests, created_at, updated_at)
                    VALUES (:id, :staff_id, :language_id, :academic_title, :degree, :biography, :research_interests, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """),
                {"id": vi_trans_id, "staff_id": str(s_id), "language_id": str(vi_lang_id), "academic_title": academic_title, "degree": degree, "biography": biography, "research_interests": research_interests}
            )

    # 5. Xóa các cột cũ và index
    op.drop_index('uidx_departments_slug', table_name='departments')
    op.drop_column('departments', 'name')
    op.drop_column('departments', 'english_name')
    op.drop_column('departments', 'description')
    op.drop_column('departments', 'slug')

    op.drop_index('uidx_positions_name', table_name='positions')
    op.drop_column('positions', 'name')
    op.drop_column('positions', 'english_name')
    op.drop_column('positions', 'description')

    op.drop_column('staffs', 'academic_title')
    op.drop_column('staffs', 'degree')
    op.drop_column('staffs', 'biography')
    op.drop_column('staffs', 'research_interests')


def downgrade() -> None:
    # Downgrade: thêm lại các cột và khôi phục dữ liệu
    op.add_column('departments', sa.Column('name', sa.String(length=255), nullable=True))
    op.add_column('departments', sa.Column('english_name', sa.String(length=255), nullable=True))
    op.add_column('departments', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('departments', sa.Column('slug', sa.String(length=255), nullable=True))

    op.add_column('positions', sa.Column('name', sa.String(length=150), nullable=True))
    op.add_column('positions', sa.Column('english_name', sa.String(length=150), nullable=True))
    op.add_column('positions', sa.Column('description', sa.Text(), nullable=True))

    op.add_column('staffs', sa.Column('academic_title', sa.String(length=50), nullable=True))
    op.add_column('staffs', sa.Column('degree', sa.String(length=100), nullable=True))
    op.add_column('staffs', sa.Column('biography', sa.Text(), nullable=True))
    op.add_column('staffs', sa.Column('research_interests', sa.Text(), nullable=True))

    connection = op.get_bind()
    vi_lang_id = connection.execute(sa.text("SELECT id FROM languages WHERE code = 'vi'")).scalar()
    en_lang_id = connection.execute(sa.text("SELECT id FROM languages WHERE code = 'en'")).scalar()

    if vi_lang_id:
        # Khôi phục departments
        dept_trans = connection.execute(
            sa.text("SELECT department_id, name, slug, description FROM department_translations WHERE language_id = :lang_id"),
            {"lang_id": str(vi_lang_id)}
        ).fetchall()
        for dept_id, name, slug, description in dept_trans:
            english_name = None
            if en_lang_id:
                english_name = connection.execute(
                    sa.text("SELECT name FROM department_translations WHERE department_id = :dept_id AND language_id = :lang_id"),
                    {"dept_id": str(dept_id), "lang_id": str(en_lang_id)}
                ).scalar()
            connection.execute(
                sa.text("""
                    UPDATE departments SET name = :name, english_name = :english_name, slug = :slug, description = :description
                    WHERE id = :id
                """),
                {"id": str(dept_id), "name": name, "english_name": english_name, "slug": slug, "description": description}
            )

        # Khôi phục positions
        pos_trans = connection.execute(
            sa.text("SELECT position_id, name, description FROM position_translations WHERE language_id = :lang_id"),
            {"lang_id": str(vi_lang_id)}
        ).fetchall()
        for pos_id, name, description in pos_trans:
            english_name = None
            if en_lang_id:
                english_name = connection.execute(
                    sa.text("SELECT name FROM position_translations WHERE position_id = :pos_id AND language_id = :lang_id"),
                    {"pos_id": str(pos_id), "lang_id": str(en_lang_id)}
                ).scalar()
            connection.execute(
                sa.text("""
                    UPDATE positions SET name = :name, english_name = :english_name, description = :description
                    WHERE id = :id
                """),
                {"id": str(pos_id), "name": name, "english_name": english_name, "description": description}
            )

        # Khôi phục staffs
        staff_trans = connection.execute(
            sa.text("SELECT staff_id, academic_title, degree, biography, research_interests FROM staff_translations WHERE language_id = :lang_id"),
            {"lang_id": str(vi_lang_id)}
        ).fetchall()
        for staff_id, academic_title, degree, biography, research_interests in staff_trans:
            connection.execute(
                sa.text("""
                    UPDATE staffs SET academic_title = :academic_title, degree = :degree, biography = :biography, research_interests = :research_interests
                    WHERE id = :id
                """),
                {"id": str(staff_id), "academic_title": academic_title, "degree": degree, "biography": biography, "research_interests": research_interests}
            )

    op.alter_column('departments', 'name', nullable=False)
    op.alter_column('departments', 'slug', nullable=False)
    op.alter_column('positions', 'name', nullable=False)

    op.create_index('uidx_departments_slug', 'departments', ['slug'], unique=True, postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index('uidx_positions_name', 'positions', ['name'], unique=True, postgresql_where=sa.text("deleted_at IS NULL"))

    op.drop_table('department_translations')
    op.drop_table('position_translations')
    op.drop_table('staff_translations')
