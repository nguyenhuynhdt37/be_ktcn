import asyncio
import sys
import os
import uuid
import httpx
from datetime import datetime, timedelta, UTC
from loguru import logger
from sqlalchemy import select

# Thêm root dự án vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import SessionLocal
from app.modules.auth.models import User
from app.modules.auth.service import hash_password
from app.modules.banner.models import Banner

async def setup_test_user():
    async with SessionLocal() as db:
        stmt = select(User).where(User.username == "admin_api_test")
        existing = await db.execute(stmt)
        user = existing.scalar_one_or_none()
        if not user:
            user_id = uuid.uuid4()
            user = User(
                id=user_id, 
                username="admin_api_test", 
                email="admin_api@test.com", 
                password_hash=hash_password("password"), 
                full_name="Admin API Test", 
                is_active=True
            )
            db.add(user)
            await db.commit()
        elif not user.is_active:
            user.is_active = True
            db.add(user)
            await db.commit()
        return "admin_api_test", "password"

async def test_banner_flow():
    username, password = await setup_test_user()
    
    from sqlalchemy import delete
    async with SessionLocal() as db:
        await db.execute(delete(Banner))
        await db.commit()
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        logger.info("🔑 1. Đăng nhập để lấy Token")
        login_res = await ac.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert login_res.status_code == 200, f"Đăng nhập thất bại: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("✅ Đăng nhập thành công!")

        # Dữ liệu test
        suffix = uuid.uuid4().hex[:6]
        
        logger.info("🏢 2. Tạo mới các banner test ở các vị trí khác nhau")
        
        # A ở HOME_HERO
        res_a = await ac.post("/api/v1/admin/banners", json={
            "title": f"Banner A {suffix}",
            "desktop_image_object_key": f"banners/desktop_a_{suffix}.jpg",
            "position": "HOME_HERO",
            "sort_order": 999
        }, headers=headers)
        assert res_a.status_code == 201
        id_a = res_a.json()["id"]
        assert res_a.json()["sort_order"] == 0

        # B ở HOME_HERO
        res_b = await ac.post("/api/v1/admin/banners", json={
            "title": f"Banner B {suffix}",
            "desktop_image_object_key": f"banners/desktop_b_{suffix}.jpg",
            "position": "HOME_HERO",
            "sort_order": 999
        }, headers=headers)
        assert res_b.status_code == 201
        id_b = res_b.json()["id"]
        assert res_b.json()["sort_order"] == 1

        # C ở NEWS_TOP
        res_c = await ac.post("/api/v1/admin/banners", json={
            "title": f"Banner C {suffix}",
            "desktop_image_object_key": f"banners/desktop_c_{suffix}.jpg",
            "position": "NEWS_TOP",
            "sort_order": 999
        }, headers=headers)
        assert res_c.status_code == 201
        id_c = res_c.json()["id"]
        assert res_c.json()["sort_order"] == 0

        # D ở HOME_HERO, chèn vào vị trí 1
        res_d = await ac.post("/api/v1/admin/banners", json={
            "title": f"Banner D {suffix}",
            "desktop_image_object_key": f"banners/desktop_d_{suffix}.jpg",
            "position": "HOME_HERO",
            "sort_order": 1
        }, headers=headers)
        assert res_d.status_code == 201
        id_d = res_d.json()["id"]
        assert res_d.json()["sort_order"] == 1

        logger.info("✅ Tạo banner thành công!")

        # 3. Kiểm tra danh sách Portal HOME_HERO
        logger.info("🔍 3. Kiểm tra API Portal và thứ tự sort_order...")
        portal_res = await ac.get("/api/v1/portal/banners?position=HOME_HERO")
        assert portal_res.status_code == 200
        items_portal = [x for x in portal_res.json() if suffix in x["title"]]
        assert len(items_portal) == 3
        # Thứ tự kì vọng: A(0), D(1), B(2)
        mapping = {x["id"]: x["sort_order"] for x in items_portal}
        assert mapping[id_a] == 0
        assert mapping[id_d] == 1
        assert mapping[id_b] == 2
        
        # Kiểm tra URL MinIO được transform đúng
        assert items_portal[0]["desktop_image_object_key"].startswith("http://")
        logger.info("✅ API Portal trả về đúng thứ tự và transform link MinIO thành công!")

        # 4. Kiểm tra phân trang Admin
        logger.info("📋 4. Kiểm tra API phân trang Admin...")
        admin_res = await ac.get("/api/v1/admin/banners?page_size=100", headers=headers)
        assert admin_res.status_code == 200
        assert admin_res.json()["total_items"] >= 4

        # 5. Di chuyển D sang NEWS_TOP
        logger.info("🔄 5. Di chuyển D sang vị trí NEWS_TOP...")
        move_res = await ac.put(f"/api/v1/admin/banners/{id_d}", json={
            "position": "NEWS_TOP",
            "sort_order": 999
        }, headers=headers)
        assert move_res.status_code == 200
        assert move_res.json()["position"] == "NEWS_TOP"
        assert move_res.json()["sort_order"] == 1 # C: 0, D: 1
        
        # Kiểm tra HOME_HERO dồn hàng
        home_res = await ac.get("/api/v1/portal/banners?position=HOME_HERO")
        home_items = [x for x in home_res.json() if suffix in x["title"]]
        assert len(home_items) == 2
        home_mapping = {x["id"]: x["sort_order"] for x in home_items}
        assert home_mapping[id_a] == 0
        assert home_mapping[id_b] == 1
        logger.info("✅ Dịch chuyển vị trí và dồn hàng tự động thành công!")

        # 6. Xóa mềm banner A
        logger.info("🗑️ 6. Xóa mềm banner A...")
        del_res = await ac.delete(f"/api/v1/admin/banners/{id_a}", headers=headers)
        assert del_res.status_code == 204
        
        # Kiểm tra HOME_HERO dồn hàng tiếp
        home_res2 = await ac.get("/api/v1/portal/banners?position=HOME_HERO")
        home_items2 = [x for x in home_res2.json() if suffix in x["title"]]
        assert len(home_items2) == 1
        assert home_items2[0]["id"] == id_b
        assert home_items2[0]["sort_order"] == 0
        logger.info("✅ Xóa mềm và dồn hàng vị trí thành công!")

        # 7. Dọn dẹp dữ liệu test
        logger.info("🧹 7. Dọn dẹp dữ liệu test...")
        for temp_id in [id_a, id_b, id_c, id_d]:
            # Xóa cứng trong database để giữ DB sạch
            async with SessionLocal() as db:
                stmt_del = select(Banner).where(Banner.id == uuid.UUID(temp_id))
                res = await db.execute(stmt_del)
                obj = res.scalar_one_or_none()
                if obj:
                    await db.delete(obj)
                    await db.commit()
        logger.info("✅ Dọn dẹp hoàn tất!")
        logger.info("🚀 TẤT CẢ CÁC BƯỚC TEST BANNER API ĐÃ VƯỢT QUA THÀNH CÔNG!")

if __name__ == "__main__":
    asyncio.run(test_banner_flow())
