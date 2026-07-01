import asyncio
import json
import uuid
from datetime import datetime
from sqlalchemy import text
from app.core.database import engine

async def restore_database():
    async with engine.begin() as conn:
        print("🚀 Bắt đầu tiến trình phân tích cứu hộ dữ liệu từ audit_logs...")

        # -------------------------------------------------------------
        # BƯỚC 1: Phục dựng cấu trúc Categories & Translations
        # -------------------------------------------------------------
        query_cats = text(
            "SELECT action, target_id, changes, created_at "
            "FROM audit_logs "
            "WHERE target_type = 'category' OR action LIKE '%CATEGORY%' "
            "ORDER BY created_at ASC;"
        )
        cat_res = await conn.execute(query_cats)
        cat_rows = cat_res.fetchall()
        print(f"📊 Tìm thấy {len(cat_rows)} log hành động liên quan đến Category.")

        categories_data = {}
        for action, target_id, changes_raw, created_at in cat_rows:
            if not target_id:
                continue
            cid = str(target_id)
            
            changes = {}
            if changes_raw:
                if isinstance(changes_raw, str):
                    try:
                        changes = json.loads(changes_raw)
                    except:
                        continue
                elif isinstance(changes_raw, dict):
                    changes = changes_raw

            if action in ("CATEGORY_CREATED", "CATEGORY_UPDATED"):
                if cid not in categories_data:
                    categories_data[cid] = {
                        "id": cid,
                        "parent_id": None,
                        "thumbnail_id": None,
                        "status": "ACTIVE",
                        "sort_order": 0,
                        "is_visible": True,
                        "is_weekly_schedule": False,
                        "is_locked": False,
                        "translations": {}
                    }
                
                # Cập nhật các trường root nếu có trong thay đổi
                for field in ["parent_id", "thumbnail_id", "status", "sort_order", "is_visible", "is_weekly_schedule", "is_locked"]:
                    if field in changes:
                        categories_data[cid][field] = changes[field]
                
                # Cập nhật thông tin dịch dạng cũ (phẳng) sang translations tiếng Việt mặc định
                for old_field in ["name", "slug", "description", "seo_title", "seo_description"]:
                    if old_field in changes:
                        if "vi" not in categories_data[cid]["translations"]:
                            categories_data[cid]["translations"]["vi"] = {}
                        categories_data[cid]["translations"]["vi"][old_field] = changes[old_field]

                # Cập nhật translations dạng cấu trúc mới (dict)
                if "translations" in changes and changes["translations"]:
                    for lang_code, trans_val in changes["translations"].items():
                        if lang_code not in categories_data[cid]["translations"]:
                            categories_data[cid]["translations"][lang_code] = {}
                        categories_data[cid]["translations"][lang_code].update(trans_val)

        # Lọc bỏ các category test nháp
        ignored_names = {"Tin học Đại cương", "Thể dục", "Thể dục quốc phòng", "ádasdasdsadasd"}
        restorable_categories = {}
        for cid, data in categories_data.items():
            vi_name = data["translations"].get("vi", {}).get("name", "")
            if vi_name in ignored_names:
                continue
            restorable_categories[cid] = data

        print(f"✅ Đã chuẩn bị phục dựng {len(restorable_categories)} danh mục thực tế.")

        # Lấy ID ngôn ngữ từ bảng languages
        lang_res = await conn.execute(text("SELECT id, code FROM languages;"))
        languages = {row[1]: str(row[0]) for row in lang_res.fetchall()}
        print(f"🌐 Các ngôn ngữ trong DB: {languages}")

        # Tracker để tránh trùng (language_id, slug)
        used_slugs = set()
        
        # Để đảm bảo tính chính xác, chúng ta select các slug hiện có trong DB trước (nếu có)
        db_slugs_res = await conn.execute(text("SELECT language_id, slug FROM category_translations;"))
        for row in db_slugs_res.fetchall():
            used_slugs.add((str(row[0]), row[1]))

        # Thực hiện chèn categories (chưa set parent_id để tránh lỗi vi phạm khóa ngoại)
        for cid, data in restorable_categories.items():
            thumbnail_id = f"'{data['thumbnail_id']}'" if data['thumbnail_id'] else "NULL"
            
            insert_cat = text(
                f"INSERT INTO categories (id, parent_id, thumbnail_id, status, sort_order, is_visible, is_weekly_schedule, is_locked, created_at, updated_at) "
                f"VALUES ('{cid}', NULL, {thumbnail_id}, '{data['status']}', {data['sort_order']}, "
                f"{data['is_visible']}, {data['is_weekly_schedule']}, {data['is_locked']}, NOW(), NOW()) "
                f"ON CONFLICT (id) DO UPDATE SET "
                f"thumbnail_id = EXCLUDED.thumbnail_id, status = EXCLUDED.status, "
                f"sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible, "
                f"is_weekly_schedule = EXCLUDED.is_weekly_schedule, is_locked = EXCLUDED.is_locked;"
            )
            await conn.execute(insert_cat)

            # Chèn các translations
            for lang_code, trans in data["translations"].items():
                lang_id = languages.get(lang_code)
                if not lang_id or not trans.get("name"):
                    continue
                
                # Tránh trùng lặp slug bằng cách thêm hậu tố ngẫu nhiên ngắn
                base_slug = trans.get("slug") or "danh-muc"
                slug_candidate = base_slug
                counter = 1
                while (lang_id, slug_candidate) in used_slugs:
                    slug_candidate = f"{base_slug}-dup-{counter}"
                    counter += 1
                
                used_slugs.add((lang_id, slug_candidate))

                tid = str(uuid.uuid4())
                name_escaped = trans.get("name").replace("'", "''")
                slug_escaped = slug_candidate.replace("'", "''")
                desc = f"'{trans.get('description').replace("'", "''")}'" if trans.get('description') else "NULL"
                seo_t = f"'{trans.get('seo_title').replace("'", "''")}'" if trans.get('seo_title') else "NULL"
                seo_d = f"'{trans.get('seo_description').replace("'", "''")}'" if trans.get('seo_description') else "NULL"
                
                insert_trans = text(
                    f"INSERT INTO category_translations (id, category_id, language_id, name, slug, description, seo_title, seo_description, created_at, updated_at) "
                    f"VALUES ('{tid}', '{cid}', '{lang_id}', '{name_escaped}', '{slug_escaped}', {desc}, {seo_t}, {seo_d}, NOW(), NOW()) "
                    f"ON CONFLICT (category_id, language_id) DO UPDATE SET "
                    f"name = EXCLUDED.name, slug = EXCLUDED.slug, description = EXCLUDED.description, "
                    f"seo_title = EXCLUDED.seo_title, seo_description = EXCLUDED.seo_description;"
                )
                await conn.execute(insert_trans)

        # Cập nhật parent_id sau khi tất cả categories đã được chèn vào DB
        print("🔗 Đang cập nhật liên kết danh mục cha (parent_id) cho các danh mục...")
        for cid, data in restorable_categories.items():
            if data["parent_id"]:
                parent_id = data["parent_id"]
                # Đảm bảo parent_id này có tồn tại trong danh mục vừa chèn
                check_parent = await conn.execute(text(f"SELECT id FROM categories WHERE id = '{parent_id}';"))
                if check_parent.scalar():
                    update_parent = text(
                        f"UPDATE categories SET parent_id = '{parent_id}' WHERE id = '{cid}';"
                    )
                    await conn.execute(update_parent)

        print("🎉 Đã khôi phục xong toàn bộ bảng categories và category_translations!")

        # -------------------------------------------------------------
        # BƯỚC 2: Khôi phục liên kết category_id trong bảng articles
        # -------------------------------------------------------------
        print("\n🔍 Đang phục dựng lại các liên kết category_id trong bảng articles...")
        query_articles = text(
            "SELECT action, target_id, changes, created_at "
            "FROM audit_logs "
            "WHERE target_type = 'article' OR action LIKE '%ARTICLE%' "
            "ORDER BY created_at ASC;"
        )
        art_res = await conn.execute(query_articles)
        art_rows = art_res.fetchall()
        print(f"📊 Tìm thấy {len(art_rows)} log hành động liên quan đến Article.")

        article_category_map = {}
        for action, target_id, changes_raw, created_at in art_rows:
            if not target_id:
                continue
            aid = str(target_id)
            
            changes = {}
            if changes_raw:
                if isinstance(changes_raw, str):
                    try:
                        changes = json.loads(changes_raw)
                    except:
                        continue
                elif isinstance(changes_raw, dict):
                    changes = changes_raw

            if action in ("ARTICLE_CREATED", "ARTICLE_UPDATED"):
                if "category_id" in changes:
                    cat_id_val = changes["category_id"]
                    if cat_id_val:
                        article_category_map[aid] = str(cat_id_val)

        print(f"✅ Đã tìm thấy {len(article_category_map)} bài viết có thông tin category liên kết trong lịch sử log.")

        restored_links_count = 0
        for aid, cat_id in article_category_map.items():
            # Kiểm tra xem category_id này có tồn tại trong các category đã được phục hồi không
            check_cat = await conn.execute(text(f"SELECT id FROM categories WHERE id = '{cat_id}';"))
            if not check_cat.scalar():
                continue
                
            # Cập nhật liên kết
            update_art = text(
                f"UPDATE articles SET category_id = '{cat_id}' WHERE id = '{aid}';"
            )
            await conn.execute(update_art)
            restored_links_count += 1

        print(f"🎉 Đã phục hồi thành công {restored_links_count} liên kết danh mục cho các bài viết!")

if __name__ == "__main__":
    asyncio.run(restore_database())
