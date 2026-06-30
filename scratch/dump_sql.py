import sys
import os

# Thêm đường dẫn thư mục backend vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.common.models.base import Base
# Import tất cả các model để đăng ký vào Base.metadata
from app.modules.auth.models import *
from app.modules.media.models import *
from app.modules.menu.models import *
from app.modules.category.models import *
from app.modules.audit.models import *
from app.modules.article.models import *
from app.modules.tag.models import *
from app.modules.faculty_staff.models import *
from app.modules.banner.models import *

from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

def dump_sql():
    sql_statements = []
    # Lấy các bảng theo thứ tự phụ thuộc khóa ngoại (sorted_tables)
    for table in Base.metadata.sorted_tables:
        # Biên dịch cấu trúc bảng theo dialect PostgreSQL
        create_table = CreateTable(table).compile(dialect=postgresql.dialect())
        sql_statements.append(str(create_table).strip() + ";")
        
    schema_sql = """-- SQL SCHEMA TOÀN HỆ THỐNG (POSTGRESQL DIALECT)
-- Tự động trích xuất từ SQLAlchemy Models của dự án
-- Ngày tạo: 2026-06-30

""" + "\n\n".join(sql_statements)
    
    output_path = '/Users/huynh/codes/be/scratch/schema.sql'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(schema_sql)
    print(f"Export SQL thành công! Đã lưu tại: {output_path}")

if __name__ == '__main__':
    dump_sql()
