import asyncio
import sys
from pathlib import Path
from sqlalchemy import select, func

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.position.models import Position, PositionTranslation
from app.modules.staff.models import Staff, StaffTranslation
from app.modules.language.models import Language

# Import all models to prevent NoReferencedTableError
from app.modules.auth.models import User, RefreshToken, LoginHistory
from app.modules.media.models import MediaItem
from app.modules.academic_title.models import AcademicTitle, AcademicTitleTranslation
from app.modules.degree.models import Degree, DegreeTranslation
from app.modules.banner.models import Banner
from app.modules.ai_hub.models import AIRequestLog
from app.modules.statistics.models import SystemStatistics
from app.modules.consultation.models import ConsultationLead
from app.modules.notification.models import Notification
from app.modules.category.models import Category, CategoryTranslation
from app.modules.menu.models import MenuItem, MenuItemTranslation
from app.modules.article.models import Article
from app.modules.tag.models import Tag
from app.modules.department.models import Department, DepartmentTranslation

async def main():
    async with SessionLocal() as db:
        print("\n================ STAFF MEMBERS AND POSITIONS ================")
        
        # Get count of staff per position
        stmt = select(Staff.position_id, func.count(Staff.id)).group_by(Staff.position_id)
        res = await db.execute(stmt)
        pos_counts = res.all()
        
        for pos_id, count in pos_counts:
            # Get position name
            pos_trans = (await db.execute(select(PositionTranslation).where(PositionTranslation.position_id == pos_id))).scalars().all()
            vi_name = next((t.name for t in pos_trans if t.language.code == "vi"), "No VI Name")
            print(f"Position ID: {pos_id} | Name: {vi_name} | Staff Count: {count}")
            
        print("\n================ ALL STAFFS IN DB ================")
        stmt = select(Staff)
        res = await db.execute(stmt)
        staffs = res.scalars().all()
        for s in staffs:
            print(f"Staff: {s.full_name} | ID: {s.id} | Slug: {s.slug} | Pos ID: {s.position_id} | Title ID: {s.academic_title_id} | Degree ID: {s.degree_id} | Dept ID: {s.department_id}")

if __name__ == "__main__":
    asyncio.run(main())
