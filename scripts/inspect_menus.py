import asyncio
import sys
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.menu.models import Menu, MenuItem, MenuItemTranslation
from app.modules.category.models import Category, CategoryTranslation
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

async def print_menu_tree(db, parent_id=None, level=0):
    stmt = (
        select(MenuItem)
        .where(MenuItem.parent_id == parent_id)
        .order_by(MenuItem.sort_order)
        .options(
            selectinload(MenuItem.translations).selectinload(MenuItemTranslation.language)
        )
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    for item in items:
        titles = ", ".join([f"[{t.language.code}: {t.title}]" for t in item.translations if t.language])
        print("  " * level + f"- ID: {item.id} | titles: {titles} | target_type: {item.target_type} | target_id: {item.target_id}")
        await print_menu_tree(db, item.id, level + 1)

async def main():
    async with SessionLocal() as db:
        # Get all menus
        stmt = select(Menu)
        result = await db.execute(stmt)
        menus = result.scalars().all()
        
        for menu in menus:
            print(f"\n================ MENU: {menu.name} (Code: {menu.code}) ================")
            await print_menu_tree(db, None, 0)

if __name__ == "__main__":
    asyncio.run(main())
