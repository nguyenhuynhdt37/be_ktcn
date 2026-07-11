import asyncio
import sys
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import selectinload

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.department.models import Department, DepartmentTranslation
from app.modules.staff.models import Staff, StaffTranslation
from app.modules.language.models import Language

# Import all models to prevent NoReferencedTableError
from app.modules.auth.models import User, RefreshToken, LoginHistory
from app.modules.media.models import MediaItem
from app.modules.position.models import Position, PositionTranslation
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

async def main():
    async with SessionLocal() as db:
        print("\n================ INSPECT DEPARTMENTS AND STAFFS ================")
        
        stmt = (
            select(Department)
            .options(
                selectinload(Department.translations),
                selectinload(Department.staffs)
            )
        )
        
        res = await db.execute(stmt)
        departments = res.scalars().all()
        
        for dept in departments:
            vi_name = next((t.name for t in dept.translations if t.language.code == "vi"), "No VI Name")
            en_name = next((t.name for t in dept.translations if t.language.code == "en"), "No EN Name")
            staff_count = len(dept.staffs)
            print(f"Dept ID: {dept.id} | Name: {vi_name} ({en_name}) | Staff count: {staff_count}")
            
            # Print staffs in this dept
            for staff in dept.staffs:
                print(f"  - Staff: {staff.full_name} | Slug: {staff.slug} | ID: {staff.id}")

if __name__ == "__main__":
    asyncio.run(main())
