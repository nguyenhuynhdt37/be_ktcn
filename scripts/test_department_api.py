import asyncio
import uuid
import sys
import os
from loguru import logger
import httpx

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import SessionLocal
from app.modules.auth.models import User
from app.core.security import hash_password

async def setup_test_user():
    from sqlalchemy import select
    async with SessionLocal() as db:
        existing = await db.execute(select(User).where(User.username == "admin_api_test"))
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
                    
        return "admin_api_test", "password"

async def test_api_flow():
    username, password = await setup_test_user()
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        logger.info("🔑 1. Đăng nhập để lấy Token")
        login_res = await ac.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert login_res.status_code == 200, f"Đăng nhập thất bại: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("✅ Đăng nhập thành công!")

        logger.info("🏢 2. Tạo mới Bộ môn")
        unique_suffix = uuid.uuid4().hex[:6]
        dept_data = {
            "name": f"Bộ môn Hệ thống thông tin điện tử {unique_suffix}",
            "english_name": "Department of Electronic Information Systems",
            "description": "Nghiên cứu và đào tạo các hệ thống thông tin điện tử thông minh.",
            "phone": "0238-123456",
            "email": "eeis@vinhuni.edu.vn",
            "website": "https://eeis.vinhuni.edu.vn",
            "office": "Phòng 404, Nhà A5",
            "sort_order": 10,
            "is_active": True
        }
        create_res = await ac.post("/api/v1/departments", json=dept_data, headers=headers)
        assert create_res.status_code == 201, f"Tạo bộ môn thất bại: {create_res.text}"
        dept_json = create_res.json()
        dept_id = dept_json["id"]
        slug = dept_json["slug"]
        logger.info(f"✅ Tạo thành công: ID={dept_id}, Slug={slug}")
        assert slug.startswith("bo-mon-he-thong-thong-tin-dien-tu")

        logger.info("🔍 3. Lấy chi tiết Bộ môn vừa tạo")
        get_res = await ac.get(f"/api/v1/departments/{dept_id}")
        assert get_res.status_code == 200
        assert get_res.json()["name"] == dept_data["name"]
        logger.info("✅ Lấy chi tiết thành công!")

        logger.info("📋 4. Lấy danh sách Bộ môn (Không cần Token - Public)")
        list_res = await ac.get("/api/v1/departments?limit=5")
        assert list_res.status_code == 200
        logger.info(f"✅ Lấy danh sách thành công, tổng số bộ môn trả về: {len(list_res.json())}")

        logger.info("🔍 5. Kiểm tra tính năng tìm kiếm bộ môn")
        search_res = await ac.get("/api/v1/departments?search=Hệ thống thông tin")
        assert search_res.status_code == 200
        search_list = search_res.json()
        assert len(search_list) >= 1
        assert any(d["id"] == str(dept_id) for d in search_list)
        logger.info("✅ Tính năng tìm kiếm hoạt động chính xác!")

        logger.info("📝 6. Cập nhật Bộ môn (Đổi tên để kiểm tra đổi slug)")
        update_data = {
            "name": f"Bộ môn Hệ thống thông tin thông minh {uuid.uuid4().hex[:6]}",
            "english_name": "Department of Smart Information Systems",
            "sort_order": 5
        }
        update_res = await ac.put(f"/api/v1/departments/{dept_id}", json=update_data, headers=headers)
        assert update_res.status_code == 200
        updated_json = update_res.json()
        new_slug = updated_json["slug"]
        logger.info(f"✅ Cập nhật thành công! Slug mới: {new_slug}")
        assert new_slug.startswith("bo-mon-he-thong-thong-tin-thong-minh")

        logger.info("🔄 7. Cập nhật Trạng thái hoạt động")
        status_res = await ac.patch(f"/api/v1/departments/{dept_id}/status", json={"is_active": False}, headers=headers)
        assert status_res.status_code == 200
        assert status_res.json()["is_active"] is False
        logger.info("✅ Cập nhật trạng thái thành công!")

        logger.info("🗑️ 8. Xóa Bộ môn (Xóa mềm)")
        delete_res = await ac.delete(f"/api/v1/departments/{dept_id}", headers=headers)
        assert delete_res.status_code == 204
        logger.info("✅ Xóa bộ môn thành công!")

        logger.info("🎯 9. Xác nhận Bộ môn đã bị xóa mềm (Không tìm thấy khi GET lại)")
        get_deleted_res = await ac.get(f"/api/v1/departments/{dept_id}")
        assert get_deleted_res.status_code == 404
        logger.info("✅ Xác thực xóa mềm thành công!")

if __name__ == "__main__":
    asyncio.run(test_api_flow())
