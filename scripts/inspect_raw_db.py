import asyncio
import sys
from pathlib import Path
from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.category.models import Category, CategoryTranslation
from app.modules.menu.models import MenuItem, MenuItemTranslation
from app.modules.language.models import Language

# Import all models to prevent NoReferencedTableError
from app.modules.auth.models import User, RefreshToken, LoginHistory
from app.modules.media.models import MediaItem
from app.modules.department.models import Department, DepartmentTranslation
from app.modules.position.models import Position, PositionTranslation
from app.modules.staff.models import Staff, StaffTranslation
from app.modules.academic_title.models import AcademicTitle, AcademicTitleTranslation
from app.modules.degree.models import Degree, DegreeTranslation
from app.modules.banner.models import Banner
from app.modules.ai_hub.models import AIRequestLog
from app.modules.statistics.models import SystemStatistics
from app.modules.consultation.models import ConsultationLead
from app.modules.notification.models import Notification
from app.modules.tag.models import Tag

async def main():
    async with SessionLocal() as db:
        res = await db.execute(select(CategoryTranslation))
        trans = res.scalars().all()
        print("--- CATEGORY TRANSLATIONS ---")
        for t in trans:
            print(f"Cat ID: {t.category_id} | Lang ID: {t.language_id} | Name: {t.name} | Slug: {t.slug}")
            
        res2 = await db.execute(select(Category))
        cats = res2.scalars().all()
        print("\n--- CATEGORIES ---")
        for c in cats:
            print(f"ID: {c.id} | Parent: {c.parent_id} | Sort: {c.sort_order}")
            
        res3 = await db.execute(select(MenuItemTranslation))
        m_trans = res3.scalars().all()
        print("\n--- MENU ITEM TRANSLATIONS ---")
        for mt in m_trans:
            print(f"MenuItem ID: {mt.menu_item_id} | Title: {mt.title}")

if __name__ == "__main__":
    asyncio.run(main())
