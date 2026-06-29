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

async def test_staff_flow():
    username, password = await setup_test_user()
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        logger.info("🔑 1. Đăng nhập để lấy Token")
        login_res = await ac.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert login_res.status_code == 200, f"Đăng nhập thất bại: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("✅ Đăng nhập thành công!")

        logger.info("🏢 Lấy Department và Position mẫu đã seed")
        depts_res = await ac.get("/api/v1/departments?page_size=1")
        assert depts_res.status_code == 200 and len(depts_res.json()["items"]) > 0
        dept_id = depts_res.json()["items"][0]["id"]
        
        pos_res = await ac.get("/api/v1/positions?page_size=1", headers=headers)
        assert pos_res.status_code == 200 and len(pos_res.json()["items"]) > 0
        pos_id = pos_res.json()["items"][0]["id"]
        logger.info(f"✅ Đã chọn Dept_ID: {dept_id} | Pos_ID: {pos_id}")

        logger.info("👨‍🏫 2. Tạo mới Giảng viên")
        unique_suffix = uuid.uuid4().hex[:6]
        staff_data = {
            "department_id": dept_id,
            "position_id": pos_id,
            "full_name": f"Nguyễn Văn A {unique_suffix}",
            "english_name": "Nguyen Van A",
            "academic_title": "Phó Giáo sư",
            "degree": "Tiến sĩ",
            "avatar_object_key": "staffs/avatars/nguyen-van-a.jpg",
            "email": f"nva_{unique_suffix}@vinhuni.edu.vn",
            "phone": "0987654321",
            "website": "https://nva.example.com",
            "office": "Phòng 301, Nhà A1",
            "biography": "Quá trình công tác dài lâu...",
            "research_interests": "Trí tuệ nhân tạo, Học máy",
            "sort_order": 5,
            "is_active": True
        }
        create_res = await ac.post("/api/v1/staffs", json=staff_data, headers=headers)
        assert create_res.status_code == 201, f"Tạo giảng viên thất bại: {create_res.text}"
        staff_json = create_res.json()
        staff_id = staff_json["id"]
        slug = staff_json["slug"]
        logger.info(f"✅ Tạo thành công: ID={staff_id}, Slug={slug}")
        assert slug.startswith("nguyen-van-a")
        # Kiểm tra transform avatar URL
        assert staff_json["avatar_object_key"].startswith("http://") or staff_json["avatar_object_key"].startswith("https://")

        logger.info("🔍 3. Lấy chi tiết Giảng viên theo ID")
        get_res = await ac.get(f"/api/v1/staffs/{staff_id}")
        assert get_res.status_code == 200
        assert get_res.json()["full_name"] == staff_data["full_name"]
        assert get_res.json()["department"]["id"] == dept_id
        assert get_res.json()["position"]["id"] == pos_id
        logger.info("✅ Lấy chi tiết qua ID thành công!")

        logger.info("🔍 4. Lấy chi tiết Giảng viên theo Slug (Public)")
        get_slug_res = await ac.get(f"/api/v1/staffs/slug/{slug}")
        assert get_slug_res.status_code == 200
        assert get_slug_res.json()["id"] == staff_id
        logger.info("✅ Lấy chi tiết qua Slug thành công!")

        logger.info("📋 5. Lấy danh sách Giảng viên phân trang (Public)")
        list_res = await ac.get("/api/v1/staffs?page=1&page_size=5")
        assert list_res.status_code == 200
        list_json = list_res.json()
        assert "items" in list_json
        assert list_json["page"] == 1
        assert len(list_json["items"]) >= 1
        logger.info(f"✅ Lấy danh sách thành công, tổng số giảng viên: {list_json['total_items']}")

        logger.info("🔎 6. Kiểm tra tìm kiếm giảng viên")
        search_res = await ac.get(f"/api/v1/staffs?search={unique_suffix}")
        assert search_res.status_code == 200
        search_items = search_res.json()["items"]
        assert len(search_items) == 1
        assert search_items[0]["id"] == staff_id
        logger.info("✅ Tìm kiếm giảng viên chính xác!")

        logger.info("📝 7. Cập nhật hồ sơ Giảng viên (Đổi tên để cập nhật slug)")
        update_data = {
            "full_name": f"Nguyễn Văn B {unique_suffix}",
            "academic_title": "Giáo sư"
        }
        update_res = await ac.put(f"/api/v1/staffs/{staff_id}", json=update_data, headers=headers)
        assert update_res.status_code == 200
        updated_json = update_res.json()
        new_slug = updated_json["slug"]
        logger.info(f"✅ Cập nhật thành công! Slug mới: {new_slug} | Học hàm mới: {updated_json['academic_title']}")
        assert new_slug.startswith("nguyen-van-b")
        assert updated_json["academic_title"] == "Giáo sư"

        logger.info("🔄 8. Cập nhật nhanh trạng thái")
        status_res = await ac.patch(f"/api/v1/staffs/{staff_id}/status", json={"is_active": False}, headers=headers)
        assert status_res.status_code == 200
        assert status_res.json()["is_active"] is False
        logger.info("✅ Cập nhật trạng thái thành công!")

        logger.info("🗑️ 9. Xóa Giảng viên (Xóa mềm)")
        delete_res = await ac.delete(f"/api/v1/staffs/{staff_id}", headers=headers)
        assert delete_res.status_code == 204
        logger.info("✅ Xóa giảng viên thành công!")

        logger.info("🎯 10. Xác nhận đã xóa mềm (GET trả về 404)")
        get_deleted_res = await ac.get(f"/api/v1/staffs/{staff_id}")
        assert get_deleted_res.status_code == 404
        logger.info("✅ Xác thực xóa mềm thành công!")

if __name__ == "__main__":
    asyncio.run(test_staff_flow())
