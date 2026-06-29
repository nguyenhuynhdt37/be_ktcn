#!/usr/bin/env python3
import asyncio
import sys
import uuid

# Đảm bảo import được thư mục gốc của dự án
sys.path.append("/Users/huynh/codes/be")

from app.core.database import SessionLocal
from app.modules.faculty_staff.models import Position
from sqlalchemy import select

# Danh sách chức vụ mặc định trong trường Đại học
SEED_POSITIONS = [
    # Ban lãnh đạo
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad01"),
        "name": "Hiệu trưởng",
        "english_name": "President / Rector",
        "description": "Người đứng đầu và đại diện pháp luật của trường đại học, chịu trách nhiệm quản lý toàn diện.",
        "sort_order": 1,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad02"),
        "name": "Phó Hiệu trưởng",
        "english_name": "Vice President / Vice Rector",
        "description": "Giúp Hiệu trưởng trong việc quản lý các lĩnh vực công tác cụ thể của trường đại học.",
        "sort_order": 2,
        "is_active": True
    },
    # Lãnh đạo Khoa / Trường
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad03"),
        "name": "Trưởng khoa",
        "english_name": "Dean",
        "description": "Chịu trách nhiệm quản lý hành chính, đào tạo và nghiên cứu khoa học trong phạm vi Khoa.",
        "sort_order": 3,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad04"),
        "name": "Phó Trưởng khoa",
        "english_name": "Vice Dean",
        "description": "Hỗ trợ Trưởng khoa quản lý các mảng công tác chuyên môn hoặc hành chính của Khoa.",
        "sort_order": 4,
        "is_active": True
    },
    # Lãnh đạo Bộ môn
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad05"),
        "name": "Trưởng bộ môn",
        "english_name": "Head of Department",
        "description": "Quản lý hoạt động giảng dạy, nghiên cứu khoa học và phát triển chuyên môn của Bộ môn.",
        "sort_order": 5,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad06"),
        "name": "Phó Trưởng bộ môn",
        "english_name": "Deputy Head of Department",
        "description": "Hỗ trợ Trưởng bộ môn trong quản lý giảng dạy và sinh hoạt học thuật của Bộ môn.",
        "sort_order": 6,
        "is_active": True
    },
    # Giảng dạy
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad07"),
        "name": "Giáo sư",
        "english_name": "Professor",
        "description": "Chức danh học thuật cao cấp nhất của giảng viên, chịu trách nhiệm giảng dạy và nghiên cứu chuyên sâu.",
        "sort_order": 7,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad08"),
        "name": "Phó Giáo sư",
        "english_name": "Associate Professor",
        "description": "Chức danh học thuật cao cấp của giảng viên, tham gia giảng dạy và nghiên cứu khoa học.",
        "sort_order": 8,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad09"),
        "name": "Giảng viên cao cấp",
        "english_name": "Senior Lecturer",
        "description": "Giảng viên có kinh nghiệm, thực hiện giảng dạy các học phần chuyên sâu và hướng dẫn khoa học.",
        "sort_order": 9,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad10"),
        "name": "Giảng viên chính",
        "english_name": "Principal Lecturer",
        "description": "Giảng viên có năng lực chuyên môn cao, đảm nhận giảng dạy và nghiên cứu khoa học chủ chốt.",
        "sort_order": 10,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad11"),
        "name": "Giảng viên",
        "english_name": "Lecturer",
        "description": "Giảng dạy các học phần được phân công, hướng dẫn đồ án, khóa luận và tham gia nghiên cứu.",
        "sort_order": 11,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad12"),
        "name": "Trợ giảng",
        "english_name": "Teaching Assistant",
        "description": "Hỗ trợ giảng viên chính trong việc chấm bài, hướng dẫn thảo luận hoặc thực hành lý thuyết.",
        "sort_order": 12,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad13"),
        "name": "Giảng viên thỉnh giảng",
        "english_name": "Visiting Lecturer",
        "description": "Giảng viên ngoài trường được mời tham gia giảng dạy theo hợp đồng thỉnh giảng.",
        "sort_order": 13,
        "is_active": True
    },
    # Nghiên cứu
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad14"),
        "name": "Nghiên cứu viên cao cấp",
        "english_name": "Senior Researcher",
        "description": "Chủ trì các đề tài khoa học lớn, viết công bố quốc tế và định hướng phát triển học thuật.",
        "sort_order": 14,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad15"),
        "name": "Nghiên cứu viên chính",
        "english_name": "Principal Researcher",
        "description": "Nghiên cứu viên có năng lực nghiên cứu độc lập cao, chủ trì các đề tài, dự án khoa học.",
        "sort_order": 15,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad16"),
        "name": "Nghiên cứu viên",
        "english_name": "Researcher",
        "description": "Thực hiện các đề tài nghiên cứu khoa học, chuyển giao công nghệ và xuất bản bài báo.",
        "sort_order": 16,
        "is_active": True
    },
    # Quản lý đào tạo
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad17"),
        "name": "Cố vấn học tập",
        "english_name": "Academic Advisor",
        "description": "Tư vấn, hỗ trợ sinh viên về học tập, định hướng nghề nghiệp và kế hoạch đào tạo.",
        "sort_order": 17,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad18"),
        "name": "Chủ nhiệm lớp",
        "english_name": "Homeroom Teacher",
        "description": "Quản lý, theo dõi và hỗ trợ các hoạt động của lớp sinh viên được phân công.",
        "sort_order": 18,
        "is_active": True
    },
    # Khác
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad19"),
        "name": "Chuyên viên",
        "english_name": "Specialist",
        "description": "Thực hiện các công việc chuyên môn nghiệp vụ tại các phòng, ban, trung tâm.",
        "sort_order": 19,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad20"),
        "name": "Kỹ thuật viên",
        "english_name": "Technician",
        "description": "Quản lý và vận hành phòng thí nghiệm, chuẩn bị trang thiết bị cho các buổi thực hành.",
        "sort_order": 20,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad21"),
        "name": "Thư ký",
        "english_name": "Secretary",
        "description": "Thực hiện công tác văn thư, hành chính, tiếp đón và hỗ trợ lịch trình làm việc.",
        "sort_order": 21,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad22"),
        "name": "Cán bộ",
        "english_name": "Staff / Officer",
        "description": "Cán bộ thực hiện các nhiệm vụ chung của đơn vị theo phân công.",
        "sort_order": 22,
        "is_active": True
    },
    {
        "id": uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad23"),
        "name": "Khác",
        "english_name": "Other",
        "description": "Các chức vụ khác chưa được phân loại cụ thể trong hệ thống.",
        "sort_order": 23,
        "is_active": True
    }
]


async def seed():
    print("⏳ Đang tiến hành gieo hạt dữ liệu Positions...")
    async with SessionLocal() as session:
        added = 0
        skipped = 0
        for pos_data in SEED_POSITIONS:
            # Kiểm tra xem trùng ID hoặc trùng Name đang hoạt động
            stmt = select(Position).where(
                (Position.id == pos_data["id"]) |
                ((Position.name == pos_data["name"]) & (Position.deleted_at.is_(None)))
            )
            res = await session.execute(stmt)
            db_obj = res.scalars().first()

            if db_obj:
                print(f"⏭️ Bỏ qua Position đã tồn tại: {pos_data['name']}")
                skipped += 1
            else:
                # Thêm mới
                new_pos = Position(
                    id=pos_data["id"],
                    name=pos_data["name"],
                    english_name=pos_data["english_name"],
                    description=pos_data["description"],
                    sort_order=pos_data["sort_order"],
                    is_active=pos_data["is_active"]
                )
                session.add(new_pos)
                added += 1

        await session.commit()
        print(f"✅ Gieo hạt hoàn tất: {added} chức vụ mới | {skipped} chức vụ bỏ qua.")


if __name__ == "__main__":
    asyncio.run(seed())
