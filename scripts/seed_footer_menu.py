import asyncio
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.main
from app.core.database import SessionLocal
from app.modules.menu.models import Menu, MenuItem, MenuItemTranslation, MenuItemTargetType
from app.modules.language.models import Language
from sqlalchemy import select, delete


async def seed_footer():
    async with SessionLocal() as db:
        # 1. Lấy Menu Footer
        menu_stmt = select(Menu).where(Menu.code == 'footer')
        res_menu = await db.execute(menu_stmt)
        footer_menu = res_menu.scalar_one_or_none()
        
        if not footer_menu:
            print("Không tìm thấy Menu với code='footer'. Tạo mới...")
            footer_menu = Menu(
                id=uuid.uuid4(),
                name="Footer Menu",
                code="footer",
                is_active=True
            )
            db.add(footer_menu)
            await db.commit()
            await db.refresh(footer_menu)

        # 2. Xóa các menu items cũ của footer để tránh trùng lặp khi chạy lại
        print("Xóa các MenuItem cũ của Footer...")
        del_stmt = delete(MenuItem).where(MenuItem.menu_id == footer_menu.id)
        await db.execute(del_stmt)
        await db.commit()

        # 3. Lấy Language IDs
        lang_stmt = select(Language)
        res_langs = await db.execute(lang_stmt)
        langs = res_langs.scalars().all()
        lang_map = {l.code: l.id for l in langs}
        
        vi_id = lang_map.get("vi")
        en_id = lang_map.get("en")
        
        if not vi_id or not en_id:
            print("Thiếu ngôn ngữ 'vi' hoặc 'en' trong DB!")
            return

        # 4. Định nghĩa cấu trúc Footer: 3 Cột lớn (depth=1) và các link con (depth=2)
        columns = [
            {
                "titles": {"vi": "Liên kết nhanh", "en": "Quick Links"},
                "sort_order": 1,
                "children": [
                    {
                        "titles": {"vi": "Tuyển sinh", "en": "Admissions"},
                        "target_type": MenuItemTargetType.CATEGORY,
                        "target_id": uuid.UUID("48471594-291c-4305-8d7d-70a7875fe584"),
                        "sort_order": 1
                    },
                    {
                        "titles": {"vi": "Đào tạo", "en": "Training"},
                        "target_type": MenuItemTargetType.CATEGORY,
                        "target_id": uuid.UUID("00c36167-0297-4633-80c5-194bdb7391ea"),
                        "sort_order": 2
                    },
                    {
                        "titles": {"vi": "Nghiên cứu khoa học", "en": "Research"},
                        "target_type": MenuItemTargetType.CATEGORY,
                        "target_id": uuid.UUID("a4798dae-2ef9-475a-b581-a448b8912e33"),
                        "sort_order": 3
                    }
                ]
            },
            {
                "titles": {"vi": "Các khoa", "en": "Faculties"},
                "sort_order": 2,
                "children": [
                    {
                        "titles": {"vi": "Khoa CNTT", "en": "Faculty of IT"},
                        "target_type": MenuItemTargetType.DEPARTMENT,
                        "target_id": uuid.UUID("05597b7e-5999-482a-86f7-363937b1e4de"),
                        "sort_order": 1
                    },
                    {
                        "titles": {"vi": "Khoa Khoa học máy tính & AI", "en": "Faculty of CS & AI"},
                        "target_type": MenuItemTargetType.DEPARTMENT,
                        "target_id": uuid.UUID("ad04f537-60de-473a-824c-ba8f17af1f1d"),
                        "sort_order": 2
                    },
                    {
                        "titles": {"vi": "Khoa Tự động hóa", "en": "Faculty of Automation"},
                        "target_type": MenuItemTargetType.DEPARTMENT,
                        "target_id": uuid.UUID("17bea2af-23bb-4a80-9e28-27df6ec025c8"),
                        "sort_order": 3
                    },
                    {
                        "titles": {"vi": "Khoa Công nghệ kỹ thuật Ô tô", "en": "Faculty of Automotive"},
                        "target_type": MenuItemTargetType.DEPARTMENT,
                        "target_id": uuid.UUID("d4ed0343-ebfc-4f7f-9b6a-b4915123648e"),
                        "sort_order": 4
                    }
                ]
            },
            {
                "titles": {"vi": "Hỗ trợ & Liên hệ", "en": "Support & Contact"},
                "sort_order": 3,
                "children": [
                    {
                        "titles": {"vi": "Liên hệ", "en": "Contact Us"},
                        "target_type": MenuItemTargetType.CATEGORY,
                        "target_id": uuid.UUID("7a6bdf24-20d5-4106-a496-de420e6f6eba"),
                        "sort_order": 1
                    },
                    {
                        "titles": {"vi": "Cổng thông tin Đại học Vinh", "en": "Vinh University Portal"},
                        "target_type": MenuItemTargetType.EXTERNAL_LINK,
                        "external_url": "https://vinhuni.edu.vn",
                        "sort_order": 2
                    },
                    {
                        "titles": {"vi": "Cổng học viên/sinh viên", "en": "Student Portal"},
                        "target_type": MenuItemTargetType.EXTERNAL_LINK,
                        "external_url": "https://student.vinhuni.edu.vn",
                        "sort_order": 3
                    }
                ]
            }
        ]

        # 5. Thực hiện thêm các cột lớn (depth=1) và các liên kết con (depth=2)
        for col in columns:
            col_id = uuid.uuid4()
            parent_item = MenuItem(
                id=col_id,
                menu_id=footer_menu.id,
                parent_id=None,
                target_type=None,
                target_id=None,
                depth=1,
                sort_order=col["sort_order"],
                is_visible=True
            )
            db.add(parent_item)
            
            # Thêm bản dịch cột lớn
            db.add(MenuItemTranslation(
                id=uuid.uuid4(),
                menu_item_id=col_id,
                language_id=vi_id,
                title=col["titles"]["vi"]
            ))
            db.add(MenuItemTranslation(
                id=uuid.uuid4(),
                menu_item_id=col_id,
                language_id=en_id,
                title=col["titles"]["en"]
            ))
            
            # Thêm liên kết con
            for child in col["children"]:
                child_id = uuid.uuid4()
                child_item = MenuItem(
                    id=child_id,
                    menu_id=footer_menu.id,
                    parent_id=col_id,
                    target_type=child["target_type"],
                    target_id=child.get("target_id"),
                    depth=2,
                    sort_order=child["sort_order"],
                    is_visible=True
                )
                db.add(child_item)
                
                # Thêm bản dịch liên kết con
                db.add(MenuItemTranslation(
                    id=uuid.uuid4(),
                    menu_item_id=child_id,
                    language_id=vi_id,
                    title=child["titles"]["vi"],
                    external_url=child.get("external_url")
                ))
                db.add(MenuItemTranslation(
                    id=uuid.uuid4(),
                    menu_item_id=child_id,
                    language_id=en_id,
                    title=child["titles"]["en"],
                    external_url=child.get("external_url")
                ))
                
        await db.commit()
        print("🎉 Đã seed thành công cấu trúc Footer Menu mới!")


if __name__ == '__main__':
    asyncio.run(seed_footer())
