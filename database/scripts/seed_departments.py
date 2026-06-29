#!/usr/bin/env python3
import asyncio
import sys
import uuid

# Đảm bảo import được thư mục gốc của dự án
sys.path.append("/Users/huynh/codes/be")

from app.core.database import SessionLocal
from app.modules.faculty_staff.models import Department
from sqlalchemy import select

# Danh sách bộ môn mặc định
SEED_DEPARTMENTS = [
    {
        "id": uuid.UUID("b1017cf7-88b3-4f9e-c616-3e4b3c75ad01"),
        "name": "Bộ môn Hệ thống và Mạng máy tính",
        "english_name": "Department of Computer Systems and Networks",
        "slug": "he-thong-va-mang-may-tinh",
        "description": "Bộ môn Hệ thống và Mạng máy tính",
        "sort_order": 1,
        "is_active": True
    },
    {
        "id": uuid.UUID("b1017cf7-88b3-4f9e-c616-3e4b3c75ad02"),
        "name": "Bộ môn Khoa học máy tính và Công nghệ phần mềm",
        "english_name": "Department of Computer Science and Software Engineering",
        "slug": "khoa-hoc-may-tinh-va-cong-nghe-phan-mem",
        "description": "Bộ môn Khoa học máy tính và Công nghệ phần mềm",
        "sort_order": 2,
        "is_active": True
    },
    {
        "id": uuid.UUID("b1017cf7-88b3-4f9e-c616-3e4b3c75ad03"),
        "name": "Bộ môn Kỹ thuật Điện - Điện tử",
        "english_name": "Department of Electrical and Electronic Engineering",
        "slug": "ky-thuat-dien-dien-tu",
        "description": "Bộ môn Kỹ thuật Điện - Điện tử",
        "sort_order": 3,
        "is_active": True
    },
    {
        "id": uuid.UUID("b1017cf7-88b3-4f9e-c616-3e4b3c75ad04"),
        "name": "Bộ môn Kỹ thuật Điều khiển và Tự động hóa",
        "english_name": "Department of Control and Automation Engineering",
        "slug": "ky-thuat-dieu-khien-va-tu-dong-hoa",
        "description": "Bộ môn Kỹ thuật Điều khiển và Tự động hóa",
        "sort_order": 4,
        "is_active": True
    },
    {
        "id": uuid.UUID("b1017cf7-88b3-4f9e-c616-3e4b3c75ad05"),
        "name": "Bộ môn Điện tử Viễn thông",
        "english_name": "Department of Electronics and Telecommunications",
        "slug": "dien-tu-vien-thong",
        "description": "Bộ môn Điện tử Viễn thông",
        "sort_order": 5,
        "is_active": True
    },
    {
        "id": uuid.UUID("b1017cf7-88b3-4f9e-c616-3e4b3c75ad06"),
        "name": "Bộ môn Công nghệ Kỹ thuật Ô tô",
        "english_name": "Department of Automotive Engineering Technology",
        "slug": "cong-nghe-ky-thuat-o-to",
        "description": "Bộ môn Công nghệ Kỹ thuật Ô tô",
        "sort_order": 6,
        "is_active": True
    }
]

async def seed():
    print("⏳ Đang tiến hành gieo hạt dữ liệu Departments...")
    async with SessionLocal() as session:
        added = 0
        skipped = 0
        for dept_data in SEED_DEPARTMENTS:
            # Kiểm tra xem trùng ID hoặc trùng Name/Slug đang hoạt động
            stmt = select(Department).where(
                (Department.id == dept_data["id"]) |
                ((Department.name == dept_data["name"]) & (Department.deleted_at.is_(None))) |
                ((Department.slug == dept_data["slug"]) & (Department.deleted_at.is_(None)))
            )
            res = await session.execute(stmt)
            db_obj = res.scalars().first()

            if db_obj:
                print(f"⏭️ Bỏ qua Department đã tồn tại: {dept_data['name']}")
                skipped += 1
            else:
                # Thêm mới
                new_dept = Department(
                    id=dept_data["id"],
                    name=dept_data["name"],
                    english_name=dept_data["english_name"],
                    slug=dept_data["slug"],
                    description=dept_data["description"],
                    sort_order=dept_data["sort_order"],
                    is_active=dept_data["is_active"]
                )
                session.add(new_dept)
                added += 1

        await session.commit()
        print(f"✅ Gieo hạt hoàn tất: {added} bộ môn mới | {skipped} bộ môn bỏ qua.")

if __name__ == "__main__":
    asyncio.run(seed())
