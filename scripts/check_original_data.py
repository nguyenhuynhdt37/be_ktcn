import asyncio
import sys
from pathlib import Path
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.menu.models import Menu, MenuItem, MenuItemTranslation
from app.modules.category.models import Category, CategoryTranslation
from app.modules.article.models import Article
from app.modules.tag.models import Tag
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

async def print_category_tree(db, parent_id=None, level=0):
    stmt = (
        select(Category)
        .where(Category.parent_id == parent_id)
        .order_by(Category.sort_order)
        .options(selectinload(Category.translations))
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    for item in items:
        trans = item.translations
        vi_name = next((t.name for t in trans if t.language.code == "vi"), "No VI Name")
        en_name = next((t.name for t in trans if t.language.code == "en"), "No EN Name")
        
        # Count articles in this category
        count_stmt = select(func.count(Article.id)).where(Article.category_id == item.id)
        count_result = await db.execute(count_stmt)
        article_count = count_result.scalar() or 0
        
        print("  " * level + f"├─ {vi_name} | {en_name} (ID: {item.id}, Articles: {article_count})")
        await print_category_tree(db, item.id, level + 1)

async def print_menu_item_tree(db, menu_id, parent_id=None, level=0):
    stmt = (
        select(MenuItem)
        .where(and_(MenuItem.menu_id == menu_id, MenuItem.parent_id == parent_id))
        .order_by(MenuItem.sort_order)
        .options(
            selectinload(MenuItem.translations).selectinload(MenuItemTranslation.language)
        )
    )
    res = await db.execute(stmt)
    items = res.scalars().all()
    for item in items:
        vi_title = next((t.title for t in item.translations if t.language.code == "vi"), "No VI Title")
        en_title = next((t.title for t in item.translations if t.language.code == "en"), "No EN Title")
        print("  " * level + f"├─ {vi_title} | {en_title} (ID: {item.id}, TargetType: {item.target_type}, TargetID: {item.target_id})")
        await print_menu_item_tree(db, menu_id, item.id, level + 1)

async def check_menus_and_categories():
    async with SessionLocal() as db:
        # Check Categories
        print("\n================ CẤU TRÚC DANH MỤC (CATEGORIES) TOÀN BỘ ================")
        await print_category_tree(db, None, 0)

        # Check Menus
        print("\n================ CẤU TRÚC MENU TOÀN BỘ ================")
        result = await db.execute(select(Menu))
        menus = result.scalars().all()
        for menu in menus:
            print(f"\nMenu: {menu.name} (Code: {menu.code}, ID: {menu.id})")
            await print_menu_item_tree(db, menu.id, None, 0)

if __name__ == "__main__":
    asyncio.run(check_menus_and_categories())
