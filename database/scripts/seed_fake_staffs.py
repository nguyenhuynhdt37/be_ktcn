import asyncio
import sys
import os
import uuid
from loguru import logger
from sqlalchemy import select, func

# Thêm project root vào python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.modules.faculty_staff.models import Department, Position, Staff
from app.modules.faculty_staff.service import slugify

# Định nghĩa dữ liệu giảng viên giả
FAKE_STAFFS_DATA = [
    # Bộ môn 1: Hệ thống và Mạng máy tính
    {
        "dept_slug": "he-thong-va-mang-may-tinh",
        "pos_name": "Trưởng bộ môn",
        "full_name": "Nguyễn Văn Sơn",
        "english_name": "Nguyen Van Son",
        "academic_title": "Phó Giáo sư",
        "degree": "Tiến sĩ",
        "avatar_object_key": "staffs/avatars/nguyen-van-son.jpg",
        "email": "nvson@vinhuni.edu.vn",
        "phone": "0912.345.678",
        "website": "https://nvson.vinhuni.edu.vn",
        "office": "Phòng 301, Nhà A5",
        "biography": "Tốt nghiệp Tiến sĩ ngành Khoa học Máy tính tại Đại học Quốc gia Seoul năm 2015. Có nhiều năm kinh nghiệm giảng dạy và nghiên cứu về hệ thống mạng máy tính.",
        "research_interests": "Mạng máy tính không dây, IoT, An ninh mạng."
    },
    {
        "dept_slug": "he-thong-va-mang-may-tinh",
        "pos_name": "Phó Trưởng bộ môn",
        "full_name": "Trần Thị Hồng",
        "english_name": "Tran Thi Hong",
        "academic_title": None,
        "degree": "Tiến sĩ",
        "avatar_object_key": "staffs/avatars/tran-thi-hong.jpg",
        "email": "tthong@vinhuni.edu.vn",
        "phone": "0983.123.456",
        "website": None,
        "office": "Phòng 302, Nhà A5",
        "biography": "Tốt nghiệp Tiến sĩ tại Đại học Bách Khoa Hà Nội năm 2018. Tham gia giảng dạy các học phần về Hệ điều hành, Kiến trúc máy tính.",
        "research_interests": "Hệ thống nhúng, Điện toán đám mây."
    },
    {
        "dept_slug": "he-thong-va-mang-may-tinh",
        "pos_name": "Giảng viên",
        "full_name": "Phạm Minh Đức",
        "english_name": "Pham Minh Duc",
        "academic_title": None,
        "degree": "Thạc sĩ",
        "avatar_object_key": "staffs/avatars/pham-minh-duc.jpg",
        "email": "pmduc@vinhuni.edu.vn",
        "phone": "0976.555.444",
        "website": None,
        "office": "Phòng 303, Nhà A5",
        "biography": "Tốt nghiệp Thạc sĩ tại Đại học Vinh năm 2020. Giảng dạy các môn thực hành mạng, quản trị hệ thống.",
        "research_interests": "Ảo hóa mạng, Software Defined Networking (SDN)."
    },

    # Bộ môn 2: Khoa học máy tính và Công nghệ phần mềm
    {
        "dept_slug": "khoa-hoc-may-tinh-va-cong-nghe-phan-mem",
        "pos_name": "Trưởng bộ môn",
        "full_name": "Lê Hoài Nam",
        "english_name": "Le Hoai Nam",
        "academic_title": "Giáo sư",
        "degree": "Tiến sĩ",
        "avatar_object_key": "staffs/avatars/le-hoai-nam.jpg",
        "email": "lhnam@vinhuni.edu.vn",
        "phone": "0915.222.333",
        "website": "https://lhnam.example.com",
        "office": "Phòng 401, Nhà A5",
        "biography": "Tiến sĩ tại Đại học Tokyo năm 2010. Giáo sư đầu ngành về Trí tuệ Nhân tạo và Công nghệ phần mềm.",
        "research_interests": "Trí tuệ nhân tạo, Xử lý ngôn ngữ tự nhiên, Kiểm thử phần mềm."
    },
    {
        "dept_slug": "khoa-hoc-may-tinh-va-cong-nghe-phan-mem",
        "pos_name": "Phó Trưởng bộ môn",
        "full_name": "Ngô Tiến Dũng",
        "english_name": "Ngo Tien Dung",
        "academic_title": None,
        "degree": "Tiến sĩ",
        "avatar_object_key": "staffs/avatars/ngo-tien-dung.jpg",
        "email": "ntdung@vinhuni.edu.vn",
        "phone": "0944.777.888",
        "website": None,
        "office": "Phòng 402, Nhà A5",
        "biography": "Tiến sĩ Khoa học máy tính tại Đại học Bách khoa Đà Nẵng năm 2019. Nghiên cứu sâu về các mô hình phát triển phần mềm.",
        "research_interests": "Phát triển phần mềm linh hoạt (Agile), DevOps, Big Data."
    },
    {
        "dept_slug": "khoa-hoc-may-tinh-va-cong-nghe-phan-mem",
        "pos_name": "Giảng viên",
        "full_name": "Nguyễn Thị Mai",
        "english_name": "Nguyen Thi Mai",
        "academic_title": None,
        "degree": "Thạc sĩ",
        "avatar_object_key": "staffs/avatars/nguyen-thi-mai.jpg",
        "email": "ntmai@vinhuni.edu.vn",
        "phone": "0988.999.000",
        "website": None,
        "office": "Phòng 403, Nhà A5",
        "biography": "Thạc sĩ Công nghệ phần mềm. Có 5 năm kinh nghiệm làm việc tại các công ty outsource lớn trước khi về trường giảng dạy.",
        "research_interests": "Lập trình Web & Mobile, UI/UX Design."
    },

    # Bộ môn 3: Kỹ thuật Điện - Điện tử
    {
        "dept_slug": "ky-thuat-dien-dien-tu",
        "pos_name": "Trưởng bộ môn",
        "full_name": "Hoàng Xuân Tùng",
        "english_name": "Hoang Xuan Tung",
        "academic_title": "Phó Giáo sư",
        "degree": "Tiến sĩ",
        "avatar_object_key": "staffs/avatars/hoang-xuan-tung.jpg",
        "email": "hxtung@vinhuni.edu.vn",
        "phone": "0913.666.777",
        "website": None,
        "office": "Phòng 201, Nhà B1",
        "biography": "Tiến sĩ ngành Kỹ thuật Điện tử tại Đại học Paris-Sud năm 2012. Chuyên gia về các hệ thống vi mạch điện tử.",
        "research_interests": "Thiết kế vi mạch, Hệ thống nhúng điện tử."
    },
    {
        "dept_slug": "ky-thuat-dien-dien-tu",
        "pos_name": "Giảng viên",
        "full_name": "Vũ Văn Hải",
        "english_name": "Vu Van Hai",
        "academic_title": None,
        "degree": "Thạc sĩ",
        "avatar_object_key": "staffs/avatars/vu-van-hai.jpg",
        "email": "vvhai@vinhuni.edu.vn",
        "phone": "0977.888.999",
        "website": None,
        "office": "Phòng 202, Nhà B1",
        "biography": "Tốt nghiệp Thạc sĩ tại Đại học Bách Khoa TP.HCM năm 2017. Giảng dạy môn Điện tử công suất.",
        "research_interests": "Năng lượng tái tạo, Hệ thống lưới điện thông minh."
    },

    # Bộ môn 4: Kỹ thuật Điều khiển và Tự động hóa
    {
        "dept_slug": "ky-thuat-dieu-khien-va-tu-dong-hoa",
        "pos_name": "Trưởng bộ môn",
        "full_name": "Đặng Quốc Việt",
        "english_name": "Dang Quoc Viet",
        "academic_title": None,
        "degree": "Tiến sĩ",
        "avatar_object_key": "staffs/avatars/dang-quoc-viet.jpg",
        "email": "dqviet@vinhuni.edu.vn",
        "phone": "0904.333.222",
        "website": None,
        "office": "Phòng 205, Nhà B1",
        "biography": "Tiến sĩ tại Đại học kỹ thuật Munich, Đức. Giảng dạy Lý thuyết điều khiển tự động, Hệ thống điều khiển số.",
        "research_interests": "Robot học, Hệ thống điều khiển phi tuyến."
    },
    {
        "dept_slug": "ky-thuat-dieu-khien-va-tu-dong-hoa",
        "pos_name": "Giảng viên",
        "full_name": "Lâm Quang Huy",
        "english_name": "Lam Quang Huy",
        "academic_title": None,
        "degree": "Thạc sĩ",
        "avatar_object_key": "staffs/avatars/lam-quang-huy.jpg",
        "email": "lqhuy@vinhuni.edu.vn",
        "phone": "0918.444.555",
        "website": None,
        "office": "Phòng 206, Nhà B1",
        "biography": "Thạc sĩ ngành Tự động hóa. Nghiên cứu ứng dụng các thuật toán điều khiển thông minh cho nhà máy.",
        "research_interests": "Điều khiển tự động dùng PLC, SCADA."
    },

    # Bộ môn 5: Kỹ thuật Cơ khí
    {
        "dept_slug": "ky-thuat-co-khi",
        "pos_name": "Trưởng bộ môn",
        "full_name": "Phạm Văn Minh",
        "english_name": "Pham Van Minh",
        "academic_title": "Phó Giáo sư",
        "degree": "Tiến sĩ",
        "avatar_object_key": "staffs/avatars/pham-van-minh.jpg",
        "email": "pvminh@vinhuni.edu.vn",
        "phone": "0912.888.777",
        "website": None,
        "office": "Phòng 101, Nhà C1",
        "biography": "Tiến sĩ ngành Kỹ thuật cơ khí chế tạo máy tại Đại học Kỹ thuật Quốc gia Bauman Moscow năm 2008.",
        "research_interests": "Gia công cơ khí chính xác, CAD/CAM/CAE."
    },

    # Bộ môn 6: Kỹ thuật Xây dựng và Kiến trúc
    {
        "dept_slug": "ky-thuat-xay-dung-va-kien-truc",
        "pos_name": "Trưởng bộ môn",
        "full_name": "Đỗ Giang Nam",
        "english_name": "Do Giang Nam",
        "academic_title": None,
        "degree": "Tiến sĩ",
        "avatar_object_key": "staffs/avatars/do-giang-nam.jpg",
        "email": "dgnam@vinhuni.edu.vn",
        "phone": "0903.444.666",
        "website": None,
        "office": "Phòng 105, Nhà C1",
        "biography": "Tiến sĩ ngành Xây dựng Dân dụng và Công nghiệp. Có nhiều năm tư vấn thiết kế các công trình cấp tỉnh và quốc gia.",
        "research_interests": "Kết cấu bê tông cốt thép, Vật liệu xây dựng thông minh."
    }
]

async def seed_fake_staffs():
    async with SessionLocal() as db:
        logger.info("⏳ Đang truy vấn danh sách Departments và Positions từ DB...")
        
        # 1. Truy vấn Departments để map slug -> ID
        depts_res = await db.execute(select(Department).where(Department.deleted_at.is_(None)))
        depts = depts_res.scalars().all()
        dept_map = {d.slug: d.id for d in depts}
        
        # 2. Truy vấn Positions để map name -> ID
        poss_res = await db.execute(select(Position).where(Position.deleted_at.is_(None)))
        poss = poss_res.scalars().all()
        pos_map = {p.name: p.id for p in poss}
        
        # 3. Định vị giảng viên theo từng bộ môn để gán sort_order tăng dần bắt đầu từ 0
        dept_staff_counts = {}

        logger.info("👨‍🏫 Bắt đầu gieo hạt dữ liệu Giảng viên giả...")
        
        inserted_count = 0
        skipped_count = 0

        for staff_data in FAKE_STAFFS_DATA:
            dept_slug = staff_data["dept_slug"]
            pos_name = staff_data["pos_name"]
            
            # Kiểm tra department và position có tồn tại trong DB không
            if dept_slug not in dept_map:
                logger.warning(f"⏭️ Bỏ qua do Bộ môn '{dept_slug}' không tồn tại trong DB.")
                continue
            if pos_name not in pos_map:
                logger.warning(f"⏭️ Bỏ qua do Chức vụ '{pos_name}' không tồn tại trong DB.")
                continue
                
            dept_id = dept_map[dept_slug]
            pos_id = pos_map[pos_name]
            
            # Tính sort_order liên tục trong bộ môn
            if dept_slug not in dept_staff_counts:
                # Tìm xem bộ môn đó hiện tại đã có giảng viên nào chưa để lấy chỉ số bắt đầu
                existing_count_stmt = select(func.count(Staff.id)).where(
                    Staff.department_id == dept_id,
                    Staff.deleted_at.is_(None)
                )
                existing_count_res = await db.execute(existing_count_stmt)
                dept_staff_counts[dept_slug] = existing_count_res.scalar_one()
                
            sort_order = dept_staff_counts[dept_slug]
            dept_staff_counts[dept_slug] += 1
            
            # Kiểm tra xem giảng viên đã tồn tại theo email hoặc tên chưa để đảm bảo idempotent
            check_stmt = select(Staff).where(
                (Staff.email == staff_data["email"]) |
                ((Staff.full_name == staff_data["full_name"]) & (Staff.department_id == dept_id) & (Staff.deleted_at.is_(None)))
            )
            check_res = await db.execute(check_stmt)
            existing_staff = check_res.scalar_one_or_none()
            
            if existing_staff:
                logger.info(f"⏭️ Bỏ qua Giảng viên đã tồn tại: {staff_data['full_name']} ({staff_data['email']})")
                skipped_count += 1
                continue
            
            # Tạo slug giảng viên
            slug = slugify(staff_data["full_name"])
            
            # Đảm bảo slug độc nhất trong DB
            base_slug = slug
            counter = 1
            while True:
                slug_check_stmt = select(Staff).where(Staff.slug == slug, Staff.deleted_at.is_(None))
                slug_check_res = await db.execute(slug_check_stmt)
                if not slug_check_res.scalar_one_or_none():
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1

            new_staff = Staff(
                id=uuid.uuid4(),
                department_id=dept_id,
                position_id=pos_id,
                full_name=staff_data["full_name"],
                english_name=staff_data["english_name"],
                slug=slug,
                academic_title=staff_data["academic_title"],
                degree=staff_data["degree"],
                avatar_object_key=staff_data["avatar_object_key"],
                email=staff_data["email"],
                phone=staff_data["phone"],
                website=staff_data["website"],
                office=staff_data["office"],
                biography=staff_data["biography"],
                research_interests=staff_data["research_interests"],
                sort_order=sort_order,
                is_active=True
            )
            db.add(new_staff)
            inserted_count += 1
            logger.info(f"➕ Thêm giảng viên mới: {staff_data['full_name']} | Dept: {dept_slug} | Order: {sort_order}")
            
        await db.commit()
        logger.info(f"✅ Gieo hạt hoàn tất: Thêm mới {inserted_count} giảng viên | Bỏ qua {skipped_count} giảng viên.")

if __name__ == "__main__":
    asyncio.run(seed_fake_staffs())
