import asyncio
import sys
import uuid
from sqlalchemy import select, or_, and_
import unicodedata
import re

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.category.models import Category, CategoryTranslation
from app.modules.menu.models import Menu, MenuItem, MenuItemTranslation, MenuItemTargetType
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

def slugify(text: str) -> str:
    """Helper to convert string to slug"""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

async def main():
    async with SessionLocal() as db:
        print("Bắt đầu cập nhật cấu trúc DB...")
        
        # 1. Lấy Vietnamese language id
        result = await db.execute(select(Language).where(Language.code == "vi"))
        vi_lang = result.scalars().first()
        if not vi_lang:
            print("Không tìm thấy ngôn ngữ 'vi'.")
            return
            
        print(f"Language 'vi' ID: {vi_lang.id}")

        # 2. Xóa các danh mục cũ
        old_categories = [
            "Ban lãnh đạo Viện",
            "Hội đồng khoa học và đào tạo",
            "Các bộ môn",
            "Bộ môn Kỹ thuật điện - điện tử",
            "Bộ môn Điều khiển và Tự động hóa",
            "Bộ môn Điện tử Viễn thông",
            "Bộ môn Khoa học máy tính và CNPM",
            "Bộ môn Hệ thống và Mạng máy tính",
            "Bộ môn Công nghệ kỹ thuật Ô tô"
        ]
        
        # Lấy category "Giới thiệu"
        result = await db.execute(
            select(Category).join(Category.translations)
            .where(and_(
                CategoryTranslation.language_id == vi_lang.id,
                CategoryTranslation.name.ilike("%Giới thiệu%")
            ))
        )
        gioi_thieu_cat = result.scalars().first()
        
        if not gioi_thieu_cat:
            print("Không tìm thấy Category 'Giới thiệu'")
            return
            
        print(f"Tìm thấy Category 'Giới thiệu' ID: {gioi_thieu_cat.id}")

        # Tìm các category cũ cần xóa
        result = await db.execute(
            select(Category).join(Category.translations)
            .where(and_(
                CategoryTranslation.language_id == vi_lang.id,
                CategoryTranslation.name.in_(old_categories)
            ))
        )
        cats_to_delete = result.scalars().all()
        for cat in cats_to_delete:
            print(f"Đang xóa danh mục cũ: {cat.id}")
            await db.delete(cat)
            
        await db.commit()
        print("Đã xóa các danh mục cũ!")

        # 3. Thêm các danh mục mới
        new_categories = [
            ("Ban lãnh đạo Trường", gioi_thieu_cat.id),
            ("Văn phòng Trường", gioi_thieu_cat.id),
            ("Các khoa", gioi_thieu_cat.id)
        ]
        
        created_cats = {}
        for idx, (name, parent_id) in enumerate(new_categories):
            cat = Category(
                parent_id=parent_id,
                sort_order=100 + idx, # To push them down
                status="PUBLISHED",
                is_visible=True,
                is_weekly_schedule=False
            )
            db.add(cat)
            await db.flush()
            
            trans = CategoryTranslation(
                category_id=cat.id,
                language_id=vi_lang.id,
                name=name,
                slug=slugify(name)
            )
            db.add(trans)
            created_cats[name] = cat.id
            print(f"Đã thêm Category mới: {name} (ID: {cat.id})")
            
        await db.flush()
        
        # Thêm các khoa con
        cac_khoa_id = created_cats.get("Các khoa")
        if cac_khoa_id:
            khoa_con = [
                "Khoa Công nghệ thông tin",
                "Khoa Khoa học máy tính và Trí tuệ nhân tạo",
                "Khoa Công nghệ kỹ thuật Điện",
                "Khoa Điện tử và Công nghệ bán dẫn",
                "Khoa Tự động hóa",
                "Khoa Công nghệ kỹ thuật Ô tô"
            ]
            
            for idx, name in enumerate(khoa_con):
                cat = Category(
                    parent_id=cac_khoa_id,
                    sort_order=idx,
                    status="PUBLISHED",
                    is_visible=True,
                    is_weekly_schedule=False
                )
                db.add(cat)
                await db.flush()
                
                trans = CategoryTranslation(
                    category_id=cat.id,
                    language_id=vi_lang.id,
                    name=name,
                    slug=slugify(name)
                )
                db.add(trans)
                created_cats[name] = cat.id
                print(f"Đã thêm Category khoa con: {name} (ID: {cat.id})")

        # 4. Cập nhật Menu (Header Menu)
        result = await db.execute(select(Menu).where(Menu.code == "header"))
        header_menu = result.scalars().first()
        
        if header_menu:
            print(f"Tìm thấy Header Menu ID: {header_menu.id}")
            
            # Lấy Menu Item "Giới thiệu"
            result = await db.execute(
                select(MenuItem).join(MenuItem.translations)
                .where(and_(
                    MenuItem.menu_id == header_menu.id,
                    MenuItemTranslation.language_id == vi_lang.id,
                    MenuItemTranslation.title.ilike("%Giới thiệu%")
                ))
            )
            gioi_thieu_menu = result.scalars().first()
            
            if gioi_thieu_menu:
                print(f"Tìm thấy Menu Item 'Giới thiệu' ID: {gioi_thieu_menu.id}")
                
                # Xóa menu cũ
                result = await db.execute(
                    select(MenuItem).join(MenuItem.translations)
                    .where(and_(
                        MenuItem.menu_id == header_menu.id,
                        MenuItemTranslation.language_id == vi_lang.id,
                        MenuItemTranslation.title.in_(old_categories)
                    ))
                )
                menus_to_delete = result.scalars().all()
                for m in menus_to_delete:
                    print(f"Đang xóa Menu Item cũ: {m.id}")
                    await db.delete(m)
                    
                await db.flush()
                
                # Thêm menu mới
                # Parent menu cho 3 mục chính
                for name, cat_id_name in [("Ban lãnh đạo Trường", "Ban lãnh đạo Trường"), 
                                          ("Văn phòng Trường", "Văn phòng Trường"), 
                                          ("Các khoa", "Các khoa")]:
                    m = MenuItem(
                        menu_id=header_menu.id,
                        parent_id=gioi_thieu_menu.id,
                        target_type=MenuItemTargetType.CATEGORY,
                        target_id=created_cats[cat_id_name],
                        depth=2,
                        sort_order=100, # Push them below existing items like Tổng quan
                        is_visible=True
                    )
                    db.add(m)
                    await db.flush()
                    
                    t = MenuItemTranslation(
                        menu_item_id=m.id,
                        language_id=vi_lang.id,
                        title=name
                    )
                    db.add(t)
                    print(f"Đã thêm Menu Item: {name}")
                    
                    if name == "Các khoa":
                        cac_khoa_menu_id = m.id
                        # Thêm menu con cho Các khoa
                        for khoa_name in khoa_con:
                            km = MenuItem(
                                menu_id=header_menu.id,
                                parent_id=cac_khoa_menu_id,
                                target_type=MenuItemTargetType.CATEGORY,
                                target_id=created_cats[khoa_name],
                                depth=3,
                                sort_order=0,
                                is_visible=True
                            )
                            db.add(km)
                            await db.flush()
                            kt = MenuItemTranslation(
                                menu_item_id=km.id,
                                language_id=vi_lang.id,
                                title=khoa_name
                            )
                            db.add(kt)
                            print(f"Đã thêm Menu Item khoa con: {khoa_name}")

        await db.commit()
        print("Hoàn tất cập nhật cấu trúc DB!")

if __name__ == "__main__":
    asyncio.run(main())
