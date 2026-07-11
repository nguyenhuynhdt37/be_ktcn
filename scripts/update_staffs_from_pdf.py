import asyncio
import sys
import uuid
from datetime import datetime
from pathlib import Path
from sqlalchemy import select, and_, delete
import unicodedata
import re

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.department.models import Department, DepartmentTranslation
from app.modules.staff.models import Staff, StaffTranslation
from app.modules.position.models import Position, PositionTranslation
from app.modules.academic_title.models import AcademicTitle, AcademicTitleTranslation
from app.modules.degree.models import Degree, DegreeTranslation
from app.modules.language.models import Language

# Import all models to prevent NoReferencedTableError
from app.modules.auth.models import User, RefreshToken, LoginHistory
from app.modules.media.models import MediaItem
from app.modules.banner.models import Banner
from app.modules.ai_hub.models import AIRequestLog
from app.modules.statistics.models import SystemStatistics
from app.modules.consultation.models import ConsultationLead
from app.modules.notification.models import Notification
from app.modules.category.models import Category, CategoryTranslation
from app.modules.menu.models import MenuItem, MenuItemTranslation
from app.modules.article.models import Article
from app.modules.tag.models import Tag

# Normalize Vietnamese name to compare
def remove_vn_accents(input_str: str) -> str:
    s1 = ''.join(c for c in unicodedata.normalize('NFD', input_str) if unicodedata.category(c) != 'Mn')
    s1 = s1.replace('đ', 'd').replace('Đ', 'D')
    return s1

def normalize_name(name: str) -> str:
    # Normalize unicode to NFC
    name = unicodedata.normalize('NFC', name)
    name = name.lower()
    # Remove titles
    name = re.sub(r'^(ts\.|th\.s|pgs\.ts|gvc\.ths\.|gvc\.ts\.|ncs)\s+', '', name)
    name = name.replace("pgs.ts.", "").replace("gvc.ths.", "").replace("gvc.ts.", "")
    name = name.replace("ts.", "").replace("ths.", "")
    name = " ".join(name.split())
    return remove_vn_accents(name)

def slugify(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

# Data parsed from PDF
pdf_staff_data = [
    # KHOA ĐIỆN TỬ VÀ CÔNG NGHỆ BÁN DẪN
    {"name": "Lê Đình Công", "dob": "20/08/1978", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên", "dept": "Khoa Điện tử và Công nghệ bán dẫn"},
    {"name": "Nguyễn Thị Quỳnh Hoa", "dob": "15/05/1979", "academic": "Phó giáo sư", "degree": "Tiến sĩ", "position": "Giảng viên cao cấp", "dept": "Khoa Điện tử và Công nghệ bán dẫn"},
    {"name": "Lê Thị Kiều Nga", "dob": "07/03/1980", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Điện tử và Công nghệ bán dẫn"},
    {"name": "Cao Thành Nghĩa", "dob": "17/12/1980", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên", "dept": "Khoa Điện tử và Công nghệ bán dẫn"},
    {"name": "Đặng Thái Sơn", "dob": "26/12/1981", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên chính", "dept": "Khoa Điện tử và Công nghệ bán dẫn"},
    {"name": "Nguyễn Thị Kim Thu", "dob": "17/03/1981", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên", "dept": "Khoa Điện tử và Công nghệ bán dẫn"},
    {"name": "Phan Duy Tùng", "dob": "13/05/1988", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên", "dept": "Khoa Điện tử và Công nghệ bán dẫn"},

    # KHOA CÔNG NGHỆ KỸ THUẬT ĐIỆN
    {"name": "Nguyễn Tiến Dũng", "dob": "05/07/1979", "academic": "Phó giáo sư", "degree": "Tiến sĩ", "position": "Giảng viên cao cấp", "dept": "Khoa Công nghệ kỹ thuật Điện"},
    {"name": "Trần Đình Dũng", "dob": "27/12/1990", "academic": None, "degree": "Đại học", "position": "Giảng viên", "dept": "Khoa Công nghệ kỹ thuật Điện"},
    {"name": "Phạm Hoàng Nam", "dob": "03/02/1985", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ kỹ thuật Điện"},
    {"name": "Lê Hoài Nam", "dob": "04/09/1999", "academic": None, "degree": "Thạc sĩ", "position": "Trợ giảng", "dept": "Khoa Công nghệ kỹ thuật Điện"},
    {"name": "Phạm Mạnh Toàn", "dob": "06/04/1979", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ kỹ thuật Điện"},

    # KHOA TỰ ĐỘNG HOÁ
    {"name": "Mai Thế Anh", "dob": "23/01/1987", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên chính", "dept": "Khoa Tự động hóa"},
    {"name": "Lê Văn Chương", "dob": "14/03/1985", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên", "dept": "Khoa Tự động hóa"},
    {"name": "Tạ Hùng Cường", "dob": "30/11/1986", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Tự động hóa"},
    {"name": "Hoàng Võ Tùng Lâm", "dob": "09/05/1989", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Tự động hóa"},
    {"name": "Đinh Văn Nam", "dob": "09/04/1989", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên", "dept": "Khoa Tự động hóa"},
    {"name": "Hồ Sỹ Phương", "dob": "01/02/1986", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Tự động hóa"},
    {"name": "Dương Đình Tú", "dob": "10/07/1986", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên chính", "dept": "Khoa Tự động hóa"},

    # KHOA CÔNG NGHỆ THÔNG TIN
    {"name": "Đặng Hồng Lĩnh", "dob": "02/11/1973", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên chính", "dept": "Khoa Công nghệ thông tin"},
    {"name": "Hoàng Hữu Việt", "dob": "10/11/1972", "academic": "Phó giáo sư", "degree": "Tiến sĩ", "position": "Giảng viên cao cấp", "dept": "Khoa Công nghệ thông tin"},
    {"name": "Trần Văn Cảnh", "dob": "15/04/1978", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ thông tin"},
    {"name": "Nguyễn Thúy Hòa", "dob": "01/05/1994", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ thông tin"},
    {"name": "Lê Văn Minh", "dob": "20/10/1971", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên chính", "dept": "Khoa Công nghệ thông tin"},
    {"name": "Phạm Trà My", "dob": "27/09/1988", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ thông tin"},
    {"name": "Nguyễn Quang Ninh", "dob": "05/06/1971", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên chính", "dept": "Khoa Công nghệ thông tin"},
    {"name": "Nguyễn Thị Uyên", "dob": "25/02/1987", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ thông tin"},

    # KHOA KHOA HỌC MÁY TÍNH VÀ TRÍ TUỆ NHÂN TẠO
    {"name": "Phan Anh Phong", "dob": "10/11/1969", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên chính", "dept": "Khoa Khoa học máy tính và Trí tuệ nhân tạo"},
    {"name": "Võ Đức Quang", "dob": "02/11/1987", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên", "dept": "Khoa Khoa học máy tính và Trí tuệ nhân tạo"},
    {"name": "Nguyễn Thị Minh Tâm", "dob": "21/01/1980", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Khoa học máy tính và Trí tuệ nhân tạo"},
    {"name": "Hồ Thị Huyền Thương", "dob": "14/12/1975", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên chính", "dept": "Khoa Khoa học máy tính và Trí tuệ nhân tạo"},
    {"name": "Hoàng Hữu Tính", "dob": "03/02/1987", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên", "dept": "Khoa Khoa học máy tính và Trí tuệ nhân tạo"},
    {"name": "Nguyễn Hải Yến", "dob": "01/10/1998", "academic": None, "degree": "Thạc sĩ", "position": "Trợ giảng", "dept": "Khoa Khoa học máy tính và Trí tuệ nhân tạo"},

    # KHOA CÔNG NGHỆ KỸ THUẬT Ô TÔ
    {"name": "Trịnh Ngọc Hoàng", "dob": "06/04/1980", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên chính", "dept": "Khoa Công nghệ kỹ thuật Ô tô"},
    {"name": "Nguyễn Phi Cường Anh", "dob": "17/02/1995", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ kỹ thuật Ô tô"},
    {"name": "Phan Quốc Cường", "dob": "20/07/1995", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ kỹ thuật Ô tô"},
    {"name": "Phan Văn Dư", "dob": "15/05/1990", "academic": None, "degree": "Tiến sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ kỹ thuật Ô tô"},
    {"name": "Lương Ngọc Minh", "dob": "10/12/1986", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ kỹ thuật Ô tô"},
    {"name": "Nguyễn Phúc Ngọc", "dob": "30/01/1978", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ kỹ thuật Ô tô"},
    {"name": "Phan Văn Nguyên", "dob": "23/08/2000", "academic": None, "degree": "Đại học", "position": "Trợ giảng", "dept": "Khoa Công nghệ kỹ thuật Ô tô"},
    {"name": "Bùi Hà Phan", "dob": "09/12/1993", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ kỹ thuật Ô tô"},
    {"name": "Đặng Đình Thành", "dob": "02/06/2000", "academic": None, "degree": "Đại học", "position": "Trợ giảng", "dept": "Khoa Công nghệ kỹ thuật Ô tô"},
    {"name": "Nguyễn Bá Uy", "dob": "22/05/1989", "academic": None, "degree": "Thạc sĩ", "position": "Giảng viên", "dept": "Khoa Công nghệ kỹ thuật Ô tô"},

    # VĂN PHÒNG TRƯỜNG
    {"name": "Hoàng Thị Hà", "dob": "26/01/1971", "academic": None, "degree": "Đại học", "position": "Chuyên viên", "dept": "Văn phòng Trường"},
    {"name": "Đặng Thị Bích Hạnh", "dob": "21/03/1976", "academic": None, "degree": "Thạc sĩ", "position": "Chuyên viên", "dept": "Văn phòng Trường"},
    {"name": "Hoàng Cẩm Nhung", "dob": "16/03/1980", "academic": None, "degree": "Thạc sĩ", "position": "Chuyên viên", "dept": "Văn phòng Trường"}
]

async def main():
    async with SessionLocal() as db:
        print("Bắt đầu cập nhật thông tin giảng viên theo PDF...")
        
        # 1. Load Languages
        vi_lang = (await db.execute(select(Language).where(Language.code == "vi"))).scalars().first()
        en_lang = (await db.execute(select(Language).where(Language.code == "en"))).scalars().first()
        
        # 2. Helper to get or create Position
        async def get_or_create_position(vi_name: str, en_name: str) -> Position:
            # Look up translation
            stmt = select(PositionTranslation).where(
                and_(PositionTranslation.name == vi_name, PositionTranslation.language_id == vi_lang.id)
            )
            trans = (await db.execute(stmt)).scalars().first()
            if trans:
                return await db.get(Position, trans.position_id)
            
            # Create new
            pos = Position(sort_order=0, is_active=True)
            db.add(pos)
            await db.flush()
            
            db.add(PositionTranslation(position_id=pos.id, language_id=vi_lang.id, name=vi_name))
            db.add(PositionTranslation(position_id=pos.id, language_id=en_lang.id, name=en_name))
            await db.flush()
            print(f"Đã tạo Position mới: {vi_name}")
            return pos

        # Define and cache standard positions
        positions_cache = {
            "Giảng viên": await get_or_create_position("Giảng viên", "Lecturer"),
            "Giảng viên chính": await get_or_create_position("Giảng viên chính", "Senior Lecturer"),
            "Giảng viên cao cấp": await get_or_create_position("Giảng viên cao cấp", "Principal Lecturer"),
            "Chuyên viên": await get_or_create_position("Chuyên viên", "Officer"),
            "Trợ giảng": await get_or_create_position("Trợ giảng", "Teaching Assistant")
        }

        # 3. Cache Academic Titles
        academic_titles = {}
        # Get all
        stmt = select(AcademicTitleTranslation).where(AcademicTitleTranslation.language_id == vi_lang.id)
        ac_trans = (await db.execute(stmt)).scalars().all()
        for t in ac_trans:
            academic_titles[t.name.lower()] = t.academic_title_id
        
        # Map academic title names from PDF
        def get_academic_title_id(name: str):
            if not name:
                return None
            name_l = name.lower()
            if name_l in academic_titles:
                return academic_titles[name_l]
            # Try partial
            for k, v in academic_titles.items():
                if k in name_l or name_l in k:
                    return v
            return None

        # 4. Cache Degrees
        degrees = {}
        stmt = select(DegreeTranslation).where(DegreeTranslation.language_id == vi_lang.id)
        deg_trans = (await db.execute(stmt)).scalars().all()
        for d in deg_trans:
            degrees[d.name.lower()] = d.degree_id

        def get_degree_id(name: str):
            if not name:
                return None
            name_l = name.lower()
            if name_l == "đại học":
                # Map "Đại học" to "Cử nhân"
                return degrees.get("cử nhân")
            if name_l in degrees:
                return degrees[name_l]
            # Try partial
            for k, v in degrees.items():
                if k in name_l or name_l in k:
                    return v
            return None

        # 5. Cache Departments
        departments = {}
        stmt = select(DepartmentTranslation).where(DepartmentTranslation.language_id == vi_lang.id)
        dept_trans = (await db.execute(stmt)).scalars().all()
        for d in dept_trans:
            departments[d.name.lower()] = d.department_id

        def get_department_id(name: str):
            name_l = name.lower()
            if name_l in departments:
                return departments[name_l]
            for k, v in departments.items():
                if k in name_l or name_l in k:
                    return v
            return None

        # 6. Load all current staffs from DB
        stmt = select(Staff)
        res = await db.execute(stmt)
        all_db_staffs = res.scalars().all()
        
        # We will match DB staff using normalized name
        matched_db_staff_ids = set()

        # Update or Create loop
        for p_staff in pdf_staff_data:
            p_name_norm = normalize_name(p_staff["name"])
            
            # Find in DB
            db_staff = None
            for s in all_db_staffs:
                if normalize_name(s.full_name) == p_name_norm:
                    db_staff = s
                    break
            
            # Find department ID
            dept_id = get_department_id(p_staff["dept"])
            if not dept_id:
                print(f"Lỗi: Không tìm thấy phòng ban/khoa '{p_staff['dept']}' cho {p_staff['name']}")
                continue
                
            # Find degree ID
            deg_id = get_degree_id(p_staff["degree"])
            # Find academic title ID
            ac_title_id = get_academic_title_id(p_staff["academic"])
            # Find position ID
            pos_id = positions_cache[p_staff["position"]].id

            if db_staff:
                # Update existing
                db_staff.full_name = p_staff["name"]
                db_staff.slug = slugify(p_staff["name"])
                db_staff.department_id = dept_id
                db_staff.position_id = pos_id
                db_staff.academic_title_id = ac_title_id
                db_staff.degree_id = deg_id
                db_staff.is_active = True
                db_staff.deleted_at = None
                
                matched_db_staff_ids.add(db_staff.id)
                print(f"Đã cập nhật Staff: {p_staff['name']} (ID: {db_staff.id}) -> Khoa: {p_staff['dept']}")
            else:
                # Create new
                new_s = Staff(
                    full_name=p_staff["name"],
                    slug=slugify(p_staff["name"]),
                    department_id=dept_id,
                    position_id=pos_id,
                    academic_title_id=ac_title_id,
                    degree_id=deg_id,
                    is_active=True,
                    sort_order=0
                )
                db.add(new_s)
                await db.flush()
                
                db.add(StaffTranslation(staff_id=new_s.id, language_id=vi_lang.id, biography=None, research_interests=None))
                db.add(StaffTranslation(staff_id=new_s.id, language_id=en_lang.id, biography=None, research_interests=None))
                print(f"Đã thêm mới Staff: {p_staff['name']} -> Khoa: {p_staff['dept']}")

        # 7. Xử lý các staff còn lại trong DB (không có trong PDF)
        # Nếu là Nguyễn Văn A (test data) hoặc staff cũ không chuyển giao, chúng ta sẽ soft delete
        for s in all_db_staffs:
            if s.id not in matched_db_staff_ids:
                # Soft delete
                s.is_active = False
                s.deleted_at = datetime.utcnow()
                print(f"Đã dọn dẹp / Soft-delete Staff không có trong PDF: {s.full_name} (ID: {s.id})")

        # Commit transaction
        await db.commit()
        print("Cập nhật toàn bộ giảng viên theo PDF hoàn tất!")

if __name__ == "__main__":
    asyncio.run(main())
