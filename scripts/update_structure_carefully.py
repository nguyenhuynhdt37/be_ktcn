import asyncio
import sys
import uuid
from pathlib import Path
from sqlalchemy import select, and_
import unicodedata
import re

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.department.models import Department, DepartmentTranslation
from app.modules.category.models import Category, CategoryTranslation
from app.modules.menu.models import Menu, MenuItem, MenuItemTranslation, MenuItemTargetType
from app.modules.language.models import Language

# Import all models to prevent NoReferencedTableError
from app.modules.auth.models import User, RefreshToken, LoginHistory
from app.modules.media.models import MediaItem
from app.modules.position.models import Position, PositionTranslation
from app.modules.staff.models import Staff, StaffTranslation
from app.modules.academic_title.models import AcademicTitle, AcademicTitleTranslation
from app.modules.degree.models import Degree, DegreeTranslation
from app.modules.banner.models import Banner
from app.modules.ai_hub.models import AIRequestLog
from app.modules.statistics.models import SystemStatistics
from app.modules.consultation.models import ConsultationLead
from app.modules.notification.models import Notification
from app.modules.article.models import Article
from app.modules.tag.models import Tag

def slugify(text: str) -> str:
    """Helper to convert string to slug"""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

async def main():
    async with SessionLocal() as db:
        print("Bắt đầu cập nhật cấu trúc DB một cách cẩn thận...")
        
        # 1. Lấy language IDs
        vi_lang = (await db.execute(select(Language).where(Language.code == "vi"))).scalars().first()
        en_lang = (await db.execute(select(Language).where(Language.code == "en"))).scalars().first()
        if not vi_lang or not en_lang:
            print("Lỗi: Không tìm thấy ngôn ngữ vi/en.")
            return

        # =====================================================================
        # 2. CẬP NHẬT PHÒNG BAN (DEPARTMENTS) - RENAME & ADD NEW
        # =====================================================================
        dept_mappings = {
            # Old ID -> (VI Name, EN Name)
            uuid.UUID("dcf37071-9b8c-4171-90ef-b64e4754b5fb"): ("Ban lãnh đạo Trường", "School Board of Management"),
            uuid.UUID("05597b7e-5999-482a-86f7-363937b1e4de"): ("Khoa Công nghệ thông tin", "Faculty of Information Technology"),
            uuid.UUID("ad04f537-60de-473a-824c-ba8f17af1f1d"): ("Khoa Khoa học máy tính và Trí tuệ nhân tạo", "Faculty of Computer Science and Artificial Intelligence"),
            uuid.UUID("8462b8f3-d85e-4308-a2df-ffa87b87fb15"): ("Khoa Công nghệ kỹ thuật Điện", "Faculty of Electrical Engineering Technology"),
            uuid.UUID("17bea2af-23bb-4a80-9e28-27df6ec025c8"): ("Khoa Tự động hóa", "Faculty of Automation"),
            uuid.UUID("363a4f61-df54-49bb-a0aa-d14fd825af9f"): ("Khoa Điện tử và Công nghệ bán dẫn", "Faculty of Electronics and Semiconductor Technology"),
            uuid.UUID("d4ed0343-ebfc-4f7f-9b6a-b4915123648e"): ("Khoa Công nghệ kỹ thuật Ô tô", "Faculty of Automotive Engineering Technology")
        }
        
        for dept_id, (vi_name, en_name) in dept_mappings.items():
            dept = await db.get(Department, dept_id)
            if dept:
                # Update translations
                vi_trans = (await db.execute(select(DepartmentTranslation).where(
                    and_(DepartmentTranslation.department_id == dept_id, DepartmentTranslation.language_id == vi_lang.id)
                ))).scalars().first()
                if vi_trans:
                    vi_trans.name = vi_name
                    vi_trans.slug = slugify(vi_name)
                else:
                    db.add(DepartmentTranslation(department_id=dept_id, language_id=vi_lang.id, name=vi_name, slug=slugify(vi_name)))
                    
                en_trans = (await db.execute(select(DepartmentTranslation).where(
                    and_(DepartmentTranslation.department_id == dept_id, DepartmentTranslation.language_id == en_lang.id)
                ))).scalars().first()
                if en_trans:
                    en_trans.name = en_name
                    en_trans.slug = slugify(en_name)
                else:
                    db.add(DepartmentTranslation(department_id=dept_id, language_id=en_lang.id, name=en_name, slug=slugify(en_name)))
                print(f"Đã cập nhật tên Department ID {dept_id} thành: {vi_name}")
            else:
                print(f"Cảnh báo: Không tìm thấy Department với ID {dept_id}")

        # Thêm mới department: Văn phòng Trường
        vp_dept = Department(sort_order=50, is_active=True)
        db.add(vp_dept)
        await db.flush()
        
        db.add(DepartmentTranslation(department_id=vp_dept.id, language_id=vi_lang.id, name="Văn phòng Trường", slug=slugify("Văn phòng Trường")))
        db.add(DepartmentTranslation(department_id=vp_dept.id, language_id=en_lang.id, name="School Office", slug=slugify("School Office")))
        print(f"Đã tạo Department mới 'Văn phòng Trường' (ID: {vp_dept.id})")

        # =====================================================================
        # 3. CẬP NHẬT DANH MỤC (CATEGORIES) - RENAME & MOVE & ADD NEW
        # =====================================================================
        gioi_thieu_cat_id = uuid.UUID("6f5dcc8f-9adf-4904-a333-2274f10d4f78")
        co_cau_cat_id = uuid.UUID("91458717-4936-4f47-9c27-93a69a16e8ea")
        
        # 3.1 Di chuyển danh mục Cơ cấu tổ chức dưới danh mục Giới thiệu
        co_cau_cat = await db.get(Category, co_cau_cat_id)
        if co_cau_cat:
            co_cau_cat.parent_id = gioi_thieu_cat_id
            print("Đã di chuyển Category 'Cơ cấu tổ chức' làm con của 'Giới thiệu'")
            
        # 3.2 Xóa danh mục Hội đồng khoa học và đào tạo
        hoi_dong_cat = await db.get(Category, uuid.UUID("76f9ae74-ce91-42bb-9b9b-30444575327c"))
        if hoi_dong_cat:
            await db.delete(hoi_dong_cat)
            print("Đã xóa Category 'Hội đồng khoa học và đào tạo'")

        # 3.3 Rename & Move 'Ban lãnh đạo Viện' -> 'Ban lãnh đạo Trường' dưới 'Giới thiệu'
        ban_ld_cat = await db.get(Category, uuid.UUID("b364d374-8fd1-4c77-a7c0-3d6366293d60"))
        if ban_ld_cat:
            ban_ld_cat.parent_id = gioi_thieu_cat_id
            vi_trans = (await db.execute(select(CategoryTranslation).where(
                and_(CategoryTranslation.category_id == ban_ld_cat.id, CategoryTranslation.language_id == vi_lang.id)
            ))).scalars().first()
            if vi_trans:
                vi_trans.name = "Ban lãnh đạo Trường"
                vi_trans.slug = slugify("Ban lãnh đạo Trường")
            en_trans = (await db.execute(select(CategoryTranslation).where(
                and_(CategoryTranslation.category_id == ban_ld_cat.id, CategoryTranslation.language_id == en_lang.id)
            ))).scalars().first()
            if en_trans:
                en_trans.name = "School Board of Management"
                en_trans.slug = slugify("School Board of Management")
            print("Đã cập nhật & di chuyển Category 'Ban lãnh đạo Trường'")

        # 3.4 Rename & Move 'Các bộ môn' -> 'Các khoa' dưới 'Giới thiệu'
        cac_bo_mon_cat = await db.get(Category, uuid.UUID("6bc9c9d1-ba3a-415c-bc5d-b05e0d061547"))
        if cac_bo_mon_cat:
            cac_bo_mon_cat.parent_id = gioi_thieu_cat_id
            vi_trans = (await db.execute(select(CategoryTranslation).where(
                and_(CategoryTranslation.category_id == cac_bo_mon_cat.id, CategoryTranslation.language_id == vi_lang.id)
            ))).scalars().first()
            if vi_trans:
                vi_trans.name = "Các khoa"
                vi_trans.slug = slugify("Các khoa")
            en_trans = (await db.execute(select(CategoryTranslation).where(
                and_(CategoryTranslation.category_id == cac_bo_mon_cat.id, CategoryTranslation.language_id == en_lang.id)
            ))).scalars().first()
            if en_trans:
                en_trans.name = "Faculties"
                en_trans.slug = slugify("Faculties")
            print("Đã cập nhật & di chuyển Category 'Các khoa'")

        # 3.5 Cập nhật các khoa con dưới 'Các khoa' (Đổi tên 6 bộ môn con)
        cat_mappings = {
            uuid.UUID("03cdd2dc-fb63-4c4f-862f-6af3ed79e79d"): ("Khoa Công nghệ kỹ thuật Điện", "Faculty of Electrical Engineering Technology"),
            uuid.UUID("dcc38992-662b-4721-be07-633a53e75eac"): ("Khoa Tự động hóa", "Faculty of Automation"),
            uuid.UUID("d56847cd-3db9-4f3c-80e7-538f9bcde32c"): ("Khoa Điện tử và Công nghệ bán dẫn", "Faculty of Electronics and Semiconductor Technology"),
            uuid.UUID("482959d4-163d-4370-ad3e-da034124ee29"): ("Khoa Khoa học máy tính và Trí tuệ nhân tạo", "Faculty of Computer Science and Artificial Intelligence"),
            uuid.UUID("0e4dde2b-d7de-4ac0-80d3-5d10ed585e75"): ("Khoa Công nghệ thông tin", "Faculty of Information Technology"),
            uuid.UUID("41292de2-1d6d-4fe3-86be-88e6117d1619"): ("Khoa Công nghệ kỹ thuật Ô tô", "Faculty of Automotive Engineering Technology")
        }
        
        for cat_id, (vi_name, en_name) in cat_mappings.items():
            cat = await db.get(Category, cat_id)
            if cat:
                vi_trans = (await db.execute(select(CategoryTranslation).where(
                    and_(CategoryTranslation.category_id == cat_id, CategoryTranslation.language_id == vi_lang.id)
                ))).scalars().first()
                if vi_trans:
                    vi_trans.name = vi_name
                    vi_trans.slug = slugify(vi_name)
                en_trans = (await db.execute(select(CategoryTranslation).where(
                    and_(CategoryTranslation.category_id == cat_id, CategoryTranslation.language_id == en_lang.id)
                ))).scalars().first()
                if en_trans:
                    en_trans.name = en_name
                    en_trans.slug = slugify(en_name)
                print(f"Đã cập nhật Category con: {vi_name}")

        # 3.6 Thêm các danh mục mới dưới 'Giới thiệu'
        new_cats = [
            ("Văn phòng Trường", "School Office"),
            ("Tổng quan", "Overview"),
            ("Sứ mệnh - Tầm nhìn", "Mission - Vision"),
            ("Đội ngũ giảng viên", "Academic Staff"),
            ("Cán bộ - Chuyên viên", "Administrative Staff"),
            ("Liên hệ", "Contact")
        ]
        
        created_cats = {}
        for idx, (vi_name, en_name) in enumerate(new_cats):
            cat = Category(
                parent_id=gioi_thieu_cat_id,
                sort_order=10 + idx,
                status="PUBLISHED",
                is_visible=True
            )
            db.add(cat)
            await db.flush()
            
            db.add(CategoryTranslation(category_id=cat.id, language_id=vi_lang.id, name=vi_name, slug=slugify(vi_name)))
            db.add(CategoryTranslation(category_id=cat.id, language_id=en_lang.id, name=en_name, slug=slugify(en_name)))
            created_cats[vi_name] = cat.id
            print(f"Đã thêm Category mới dưới 'Giới thiệu': {vi_name}")

        # =====================================================================
        # 4. CẬP NHẬT HEADER MENU
        # =====================================================================
        gioi_thieu_menu_id = uuid.UUID("0f9582f4-1bcc-4327-9c0d-aaf829e47289")
        co_cau_menu_id = uuid.UUID("926663c7-2fa7-4242-8ab7-15bff3b8bc3a")
        
        # 4.1 Di chuyển 'Cơ cấu tổ chức' menu dưới 'Giới thiệu'
        co_cau_menu = await db.get(MenuItem, co_cau_menu_id)
        if co_cau_menu:
            co_cau_menu.parent_id = gioi_thieu_menu_id
            co_cau_menu.depth = 2
            co_cau_menu.target_type = MenuItemTargetType.CATEGORY
            co_cau_menu.target_id = co_cau_cat_id
            print("Đã di chuyển Menu Item 'Cơ cấu tổ chức' dưới 'Giới thiệu'")

        # 4.2 Xóa Menu Item 'Hội đồng khoa học và đào tạo'
        hoi_dong_menu = await db.get(MenuItem, uuid.UUID("2bfca7a6-111a-47d3-b98b-2863365ee6a2"))
        if hoi_dong_menu:
            await db.delete(hoi_dong_menu)
            print("Đã xóa Menu Item 'Hội đồng khoa học và đào tạo'")

        # 4.3 Rename & Move 'Ban lãnh đạo Viện' -> 'Ban lãnh đạo' dưới 'Giới thiệu'
        ban_ld_menu = await db.get(MenuItem, uuid.UUID("d1821e1a-d349-43a6-9c22-63b9ebfdec3d"))
        if ban_ld_menu:
            ban_ld_menu.parent_id = gioi_thieu_menu_id
            ban_ld_menu.depth = 2
            ban_ld_menu.target_type = MenuItemTargetType.DEPARTMENT
            ban_ld_menu.target_id = uuid.UUID("dcf37071-9b8c-4171-90ef-b64e4754b5fb") # Ban lãnh đạo Trường dept
            
            vi_t = (await db.execute(select(MenuItemTranslation).where(
                and_(MenuItemTranslation.menu_item_id == ban_ld_menu.id, MenuItemTranslation.language_id == vi_lang.id)
            ))).scalars().first()
            if vi_t:
                vi_t.title = "Ban lãnh đạo"
            en_t = (await db.execute(select(MenuItemTranslation).where(
                and_(MenuItemTranslation.menu_item_id == ban_ld_menu.id, MenuItemTranslation.language_id == en_lang.id)
            ))).scalars().first()
            if en_t:
                en_t.title = "Board of Management"
            print("Đã cập nhật & di chuyển Menu Item 'Ban lãnh đạo'")

        # 4.4 Rename & Move 'Các bộ môn' -> 'Các khoa' dưới 'Giới thiệu'
        cac_bo_mon_menu = await db.get(MenuItem, uuid.UUID("81d31a4e-e1bd-4a5a-bbe2-4b85b4a7a0fd"))
        if cac_bo_mon_menu:
            cac_bo_mon_menu.parent_id = gioi_thieu_menu_id
            cac_bo_mon_menu.depth = 2
            cac_bo_mon_menu.target_type = None
            cac_bo_mon_menu.target_id = None
            
            vi_t = (await db.execute(select(MenuItemTranslation).where(
                and_(MenuItemTranslation.menu_item_id == cac_bo_mon_menu.id, MenuItemTranslation.language_id == vi_lang.id)
            ))).scalars().first()
            if vi_t:
                vi_t.title = "Các khoa"
            en_t = (await db.execute(select(MenuItemTranslation).where(
                and_(MenuItemTranslation.menu_item_id == cac_bo_mon_menu.id, MenuItemTranslation.language_id == en_lang.id)
            ))).scalars().first()
            if en_t:
                en_t.title = "Faculties"
            print("Đã cập nhật & di chuyển Menu Item 'Các khoa'")

        # 4.5 Cập nhật các menu khoa con dưới 'Các khoa' (Đổi tên & cập nhật target_type / target_id)
        menu_mappings = {
            uuid.UUID("5e9e1c32-dcc3-430a-9f7b-ccee0e42396a"): ("Khoa Công nghệ kỹ thuật Điện", "Faculty of Electrical Engineering Technology", uuid.UUID("8462b8f3-d85e-4308-a2df-ffa87b87fb15")),
            uuid.UUID("515e8289-134d-40d0-9dc1-bd4c2e3e0dac"): ("Khoa Tự động hóa", "Faculty of Automation", uuid.UUID("17bea2af-23bb-4a80-9e28-27df6ec025c8")),
            uuid.UUID("7490580f-2fe1-4787-8f1f-071bc868a124"): ("Khoa Điện tử và Công nghệ bán dẫn", "Faculty of Electronics and Semiconductor Technology", uuid.UUID("363a4f61-df54-49bb-a0aa-d14fd825af9f")),
            uuid.UUID("2d71c99f-093f-45ff-93f9-11ec63220e97"): ("Khoa Khoa học máy tính và Trí tuệ nhân tạo", "Faculty of Computer Science and Artificial Intelligence", uuid.UUID("ad04f537-60de-473a-824c-ba8f17af1f1d")),
            uuid.UUID("480ff363-bc58-4bd8-a53e-dacbee1fc47e"): ("Khoa Công nghệ thông tin", "Faculty of Information Technology", uuid.UUID("05597b7e-5999-482a-86f7-363937b1e4de")),
            uuid.UUID("883787b8-f355-407c-bcb4-5fd80e166256"): ("Khoa Công nghệ kỹ thuật Ô tô", "Faculty of Automotive Engineering Technology", uuid.UUID("d4ed0343-ebfc-4f7f-9b6a-b4915123648e"))
        }
        
        for menu_item_id, (vi_title, en_title, target_dept_id) in menu_mappings.items():
            m_item = await db.get(MenuItem, menu_item_id)
            if m_item:
                m_item.depth = 3
                m_item.target_type = MenuItemTargetType.DEPARTMENT
                m_item.target_id = target_dept_id
                
                vi_t = (await db.execute(select(MenuItemTranslation).where(
                    and_(MenuItemTranslation.menu_item_id == menu_item_id, MenuItemTranslation.language_id == vi_lang.id)
                ))).scalars().first()
                if vi_t:
                    vi_t.title = vi_title
                en_t = (await db.execute(select(MenuItemTranslation).where(
                    and_(MenuItemTranslation.menu_item_id == menu_item_id, MenuItemTranslation.language_id == en_lang.id)
                ))).scalars().first()
                if en_t:
                    en_t.title = en_title
                print(f"Đã cập nhật Menu Item khoa con: {vi_title}")

        # 4.6 Làm phẳng cấu trúc menu con dưới 'Cơ cấu tổ chức' để tránh vi phạm độ sâu tối đa = 3
        # ID của 'Các tổ chức đoàn thể' Menu Item: 8547d708-2c21-4fa5-927c-0cf11251b8a8
        doan_the_menu = await db.get(MenuItem, uuid.UUID("8547d708-2c21-4fa5-927c-0cf11251b8a8"))
        if doan_the_menu:
            doan_the_menu.depth = 3
            
            # Cập nhật các menu con của nó lên làm con trực tiếp của 'Cơ cấu tổ chức' (depth 3)
            doan_the_children_ids = [
                uuid.UUID("ced98e5a-fe83-4d90-94f6-6d528c87db27"), # Công đoàn
                uuid.UUID("e2544ace-1b4f-48e0-ba22-ebe4bf0bbf32")  # Đoàn thanh niên...
            ]
            for child_id in doan_the_children_ids:
                child_menu = await db.get(MenuItem, child_id)
                if child_menu:
                    child_menu.parent_id = co_cau_menu_id # Move to Cơ cấu tổ chức directly
                    child_menu.depth = 3
                    print(f"Đã làm phẳng Menu Item: {child_id}")

        # 4.7 Thêm Menu Item mới cho 'Văn phòng Trường' dưới 'Giới thiệu'
        vp_menu = MenuItem(
            menu_id=uuid.UUID("a0000000-0000-4000-a000-000000000001"),
            parent_id=gioi_thieu_menu_id,
            target_type=MenuItemTargetType.DEPARTMENT,
            target_id=vp_dept.id,
            depth=2,
            sort_order=40,
            is_visible=True
        )
        db.add(vp_menu)
        await db.flush()
        
        db.add(MenuItemTranslation(menu_item_id=vp_menu.id, language_id=vi_lang.id, title="Văn phòng Trường"))
        db.add(MenuItemTranslation(menu_item_id=vp_menu.id, language_id=en_lang.id, title="School Office"))
        print(f"Đã tạo Menu Item 'Văn phòng Trường' (ID: {vp_menu.id})")

        # 4.8 Thêm các Menu Items mới khác dưới 'Giới thiệu'
        new_menus = [
            ("Tổng quan", "Overview", MenuItemTargetType.CATEGORY, created_cats["Tổng quan"], 10),
            ("Sứ mệnh - Tầm nhìn", "Mission - Vision", MenuItemTargetType.CATEGORY, created_cats["Sứ mệnh - Tầm nhìn"], 30),
            ("Đội ngũ giảng viên", "Academic Staff", MenuItemTargetType.CATEGORY, created_cats["Đội ngũ giảng viên"], 60),
            ("Liên hệ", "Contact", MenuItemTargetType.CATEGORY, created_cats["Liên hệ"], 80)
        ]
        
        for vi_title, en_title, t_type, t_id, s_order in new_menus:
            nm = MenuItem(
                menu_id=uuid.UUID("a0000000-0000-4000-a000-000000000001"),
                parent_id=gioi_thieu_menu_id,
                target_type=t_type,
                target_id=t_id,
                depth=2,
                sort_order=s_order,
                is_visible=True
            )
            db.add(nm)
            await db.flush()
            db.add(MenuItemTranslation(menu_item_id=nm.id, language_id=vi_lang.id, title=vi_title))
            db.add(MenuItemTranslation(menu_item_id=nm.id, language_id=en_lang.id, title=en_title))
            print(f"Đã thêm Menu Item mới: {vi_title}")

        # LƯU THAY ĐỔI
        await db.commit()
        print("Hoàn tất cập nhật cấu trúc DB một cách cẩn thận và an toàn!")

if __name__ == "__main__":
    asyncio.run(main())
