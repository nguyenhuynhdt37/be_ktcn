import asyncio
import sys
from pathlib import Path
from sqlalchemy import select, func

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.position.models import Position, PositionTranslation
from app.modules.degree.models import Degree, DegreeTranslation
from app.modules.academic_title.models import AcademicTitle, AcademicTitleTranslation
from app.modules.department.models import Department, DepartmentTranslation
from app.modules.staff.models import Staff
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

async def main():
    async with SessionLocal() as db:
        print("\n=== KIỂM TRA DỮ LIỆU SEED RÁC ===")
        
        # 1. Kiểm tra Positions
        print("\n--- POSITIONS ---")
        stmt = select(Position)
        positions = (await db.execute(stmt)).scalars().all()
        for p in positions:
            vi_name = next((t.name for t in p.translations if t.language.code == "vi"), "No VI Name")
            en_name = next((t.name for t in p.translations if t.language.code == "en"), "No EN Name")
            
            # Check usage in active staffs
            active_usage = (await db.execute(
                select(func.count(Staff.id)).where(and_(Staff.position_id == p.id, Staff.is_active == True, Staff.deleted_at == None))
            )).scalar()
            
            is_trash = "No VI Name" in vi_name or "Dept" in vi_name or "test" in vi_name.lower() or active_usage == 0
            # Wait, some real positions might have 0 active usage temporarily, but let's highlight them.
            # Real positions in seed should be kept, e.g. "Chủ tịch Công đoàn", "Trưởng bộ môn", "Phó Trưởng Bộ môn" etc.
            status = "🚨 RÁC/UNUSED" if is_trash else "✅ OK"
            print(f"ID: {p.id} | VI: {vi_name} | EN: {en_name} | Active Staff Usage: {active_usage} | {status}")

        # 2. Kiểm tra Degrees
        print("\n--- DEGREES ---")
        stmt = select(Degree)
        degrees = (await db.execute(stmt)).scalars().all()
        for d in degrees:
            vi_name = next((t.name for t in d.translations if t.language.code == "vi"), "No VI Name")
            en_name = next((t.name for t in d.translations if t.language.code == "en"), "No EN Name")
            active_usage = (await db.execute(
                select(func.count(Staff.id)).where(and_(Staff.degree_id == d.id, Staff.is_active == True, Staff.deleted_at == None))
            )).scalar()
            is_trash = "No VI Name" in vi_name or active_usage == 0
            status = "🚨 RÁC/UNUSED" if is_trash else "✅ OK"
            print(f"ID: {d.id} | VI: {vi_name} | EN: {en_name} | Active Staff Usage: {active_usage} | {status}")

        # 3. Kiểm tra Departments
        print("\n--- DEPARTMENTS ---")
        stmt = select(Department)
        departments = (await db.execute(stmt)).scalars().all()
        for dept in departments:
            vi_name = next((t.name for t in dept.translations if t.language.code == "vi"), "No VI Name")
            en_name = next((t.name for t in dept.translations if t.language.code == "en"), "No EN Name")
            active_usage = (await db.execute(
                select(func.count(Staff.id)).where(and_(Staff.department_id == dept.id, Staff.is_active == True, Staff.deleted_at == None))
            )).scalar()
            # Check if it is a real department we just updated or if it is an old dummy/test department
            is_real = vi_name in [
                "Ban lãnh đạo Trường", "Khoa Công nghệ thông tin", 
                "Khoa Khoa học máy tính và Trí tuệ nhân tạo", 
                "Khoa Công nghệ kỹ thuật Điện", "Khoa Tự động hóa", 
                "Khoa Điện tử và Công nghệ bán dẫn", 
                "Khoa Công nghệ kỹ thuật Ô tô", "Văn phòng Trường"
            ]
            is_trash = not is_real or active_usage == 0
            status = "🚨 RÁC/UNUSED" if is_trash else "✅ OK"
            print(f"ID: {dept.id} | VI: {vi_name} | EN: {en_name} | Active Staff Usage: {active_usage} | {status}")

        # 4. Kiểm tra Academic Titles
        print("\n--- ACADEMIC TITLES ---")
        stmt = select(AcademicTitle)
        academics = (await db.execute(stmt)).scalars().all()
        for a in academics:
            vi_name = next((t.name for t in a.translations if t.language.code == "vi"), "No VI Name")
            en_name = next((t.name for t in a.translations if t.language.code == "en"), "No EN Name")
            active_usage = (await db.execute(
                select(func.count(Staff.id)).where(and_(Staff.academic_title_id == a.id, Staff.is_active == True, Staff.deleted_at == None))
            )).scalar()
            is_trash = "No VI Name" in vi_name or active_usage == 0
            status = "🚨 RÁC/UNUSED" if is_trash else "✅ OK"
            print(f"ID: {a.id} | VI: {vi_name} | EN: {en_name} | Active Staff Usage: {active_usage} | {status}")

if __name__ == "__main__":
    from sqlalchemy import and_
    asyncio.run(main())
