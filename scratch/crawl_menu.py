import asyncio
import uuid
from sqlalchemy import select, delete
from bs4 import BeautifulSoup

from app.core.database import SessionLocal
from app.modules.menu.models import Menu, MenuItem, MenuItemTargetType
from app.modules.category.models import Category
from app.modules.article.models import Article
from app.modules.faculty_staff.models import Department, Position, Staff
from app.modules.auth.models import User
from app.modules.tag.models import Tag
from app.modules.banner.models import Banner
from app.modules.media.models import MediaItem
from app.modules.audit.models import AuditLog

async def resolve_menu_target(db, href: str) -> tuple[MenuItemTargetType | None, uuid.UUID | None, str | None]:
    """Phân tích link href để tự động ánh xạ tới thực thể tương ứng trong DB"""
    if not href or href == "#" or href.startswith("javascript:") or href == "":
        return MenuItemTargetType.EXTERNAL_LINK, None, "#"
        
    # Chuẩn hóa url tuyệt đối về tương đối
    href_clean = href.replace("https://vienktcn.vinhuni.edu.vn", "").replace("http://vienktcn.vinhuni.edu.vn", "")
    
    if href_clean.startswith("http://") or href_clean.startswith("https://") or href_clean.startswith("mail.google.com"):
        return MenuItemTargetType.EXTERNAL_LINK, None, href
        
    parts = [p for p in href_clean.strip("/").split("/") if p]
    if not parts:
        return MenuItemTargetType.EXTERNAL_LINK, None, "/"
        
    slug = parts[-1]
    
    # 1. Kiểm tra xem có phải Department không
    if "co-cau-to-chuc" in href_clean or "bm-" in slug or "bo-mon-" in slug:
        stmt = select(Department.id).where(Department.slug == slug)
        res = await db.execute(stmt)
        dept_id = res.scalars().first()
        if dept_id:
            return MenuItemTargetType.DEPARTMENT, dept_id, None
            
    # 2. Kiểm tra xem có phải Article không (link thường chứa /seo/)
    if "/seo/" in href_clean:
        stmt = select(Article.id).where(Article.slug == slug)
        res = await db.execute(stmt)
        art_id = res.scalars().first()
        if art_id:
            return MenuItemTargetType.ARTICLE, art_id, None
            
    # 3. Kiểm tra xem có phải Category không
    stmt = select(Category.id).where(Category.slug == slug)
    res = await db.execute(stmt)
    cat_id = res.scalars().first()
    if cat_id:
        return MenuItemTargetType.CATEGORY, cat_id, None
        
    # Mặc định coi là link ngoài/link tĩnh trong hệ thống
    return MenuItemTargetType.EXTERNAL_LINK, None, href_clean

async def get_or_create_main_menu(db) -> Menu:
    """Lấy Menu 'header' sẵn có của hệ thống"""
    stmt = select(Menu).where(Menu.code == "header")
    res = await db.execute(stmt)
    menu = res.scalars().first()
    
    if not menu:
        menu = Menu(
            name="Header Menu",
            code="header",
            description="Menu chính hiển thị trên đầu trang website",
            is_active=True
        )
        db.add(menu)
        await db.commit()
        await db.refresh(menu)
        print("Đã tạo mới Menu: 'Header Menu' (code: header)")
    else:
        # Xoá toàn bộ các MenuItem cũ thuộc Menu 'header'
        await db.execute(delete(MenuItem).where(MenuItem.menu_id == menu.id))
        await db.commit()
        print("Đã xoá sạch các mục menu cũ trong 'header' để nạp lại mới.")
        
    # Xoá menu 'main-menu' thừa nếu có
    await db.execute(delete(Menu).where(Menu.code == "main-menu"))
    await db.commit()
        
    return menu

async def main():
    print("--- BẮT ĐẦU CÀO VÀ THIẾT LẬP MENU 3 TẦNG ---")
    
    with open("/tmp/homepage.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    vinhmenu = soup.find(class_="vinhmenuhome")
    if not vinhmenu:
        print("Không tìm thấy class 'vinhmenuhome' trong file HTML trang chủ!")
        return
        
    async with SessionLocal() as db:
        menu = await get_or_create_main_menu(db)
        
        # Lấy danh sách menu cấp 1
        ul_c1 = vinhmenu.find("ul", recursive=False)
        if not ul_c1:
            # Dự phòng nếu ul đầu tiên bọc trực tiếp
            ul_c1 = vinhmenu.find("ul")
            
        if not ul_c1:
            print("Không tìm thấy thẻ ul của menu cấp 1!")
            return
            
        li_c1_list = ul_c1.find_all("li", recursive=False)
        print(f"Phát hiện {len(li_c1_list)} mục menu cấp 1")
        
        for idx_c1, li_c1 in enumerate(li_c1_list, 1):
            a_c1 = li_c1.find("a", recursive=False)
            if not a_c1:
                continue
                
            title_c1 = a_c1.text.replace(" Giới thiệu", "Giới thiệu").replace(" Đào tạo", "Đào tạo").strip()
            href_c1 = a_c1.get("href", "")
            
            target_type_c1, target_id_c1, ext_url_c1 = await resolve_menu_target(db, href_c1)
            
            # Lưu MenuItem cấp 1
            item_c1 = MenuItem(
                menu_id=menu.id,
                parent_id=None,
                title=title_c1,
                target_type=target_type_c1,
                target_id=target_id_c1,
                external_url=ext_url_c1,
                depth=1,
                sort_order=idx_c1,
                is_visible=True
            )
            db.add(item_c1)
            await db.commit()
            await db.refresh(item_c1)
            print(f"[*] Cấp 1: {title_c1} (href: {href_c1}) -> Target: {target_type_c1}")
            
            # Kiểm tra các submenu cấp 2
            ul_c2 = li_c1.find("ul")
            if not ul_c2:
                continue
                
            li_c2_list = ul_c2.find_all("li", recursive=False)
            for idx_c2, li_c2 in enumerate(li_c2_list, 1):
                a_c2 = li_c2.find("a", recursive=False)
                if not a_c2:
                    continue
                    
                title_c2 = a_c2.text.strip()
                href_c2 = a_c2.get("href", "")
                
                target_type_c2, target_id_c2, ext_url_c2 = await resolve_menu_target(db, href_c2)
                
                item_c2 = MenuItem(
                    menu_id=menu.id,
                    parent_id=item_c1.id,
                    title=title_c2,
                    target_type=target_type_c2,
                    target_id=target_id_c2,
                    external_url=ext_url_c2,
                    depth=2,
                    sort_order=idx_c2,
                    is_visible=True
                )
                db.add(item_c2)
                await db.commit()
                await db.refresh(item_c2)
                print(f"  [-] Cấp 2: {title_c2} (href: {href_c2}) -> Target: {target_type_c2}")
                
                # Kiểm tra submenu cấp 3
                ul_c3 = li_c2.find("ul")
                if not ul_c3:
                    continue
                    
                li_c3_list = ul_c3.find_all("li", recursive=False)
                for idx_c3, li_c3 in enumerate(li_c3_list, 1):
                    a_c3 = li_c3.find("a", recursive=False)
                    if not a_c3:
                        continue
                        
                    title_c3 = a_c3.text.strip()
                    href_c3 = a_c3.get("href", "")
                    
                    target_type_c3, target_id_c3, ext_url_c3 = await resolve_menu_target(db, href_c3)
                    
                    item_c3 = MenuItem(
                        menu_id=menu.id,
                        parent_id=item_c2.id,
                        title=title_c3,
                        target_type=target_type_c3,
                        target_id=target_id_c3,
                        external_url=ext_url_c3,
                        depth=3,
                        sort_order=idx_c3,
                        is_visible=True
                    )
                    db.add(item_c3)
                    await db.commit()
                    await db.refresh(item_c3)
                    print(f"    [+] Cấp 3: {title_c3} (href: {href_c3}) -> Target: {target_type_c3}")
                    
    print("\n--- HOÀN THÀNH CÀO VÀ THIẾT LẬP MENU ---")

if __name__ == "__main__":
    asyncio.run(main())
