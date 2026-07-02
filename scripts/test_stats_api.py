import asyncio
import sys
import os
import uuid
import httpx
from loguru import logger
from sqlalchemy import select

# Thêm root dự án vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import SessionLocal
from app.modules.auth.models import User
from app.modules.auth.service import hash_password

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
        return "admin_api_test", "password"

async def test_stats_endpoints():
    username, password = await setup_test_user()
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        logger.info("🔑 1. Đăng nhập để lấy Token")
        login_res = await ac.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert login_res.status_code == 200, f"Đăng nhập thất bại: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("✅ Đăng nhập thành công!")

        # ----------------------------------------------------
        # TEST DEPARTMENTS STATS
        # ----------------------------------------------------
        logger.info("🏢 2. Gọi API Thống kê Bộ môn (Departments Stats)")
        dept_stats_res = await ac.get("/api/v1/admin/departments/stats", headers=headers)
        assert dept_stats_res.status_code == 200, f"Lỗi departments stats: {dept_stats_res.text}"
        dept_data = dept_stats_res.json()
        
        # Verify structure
        for field in ["total", "active", "inactive"]:
            assert field in dept_data, f"Thiếu trường '{field}' trong response"
            assert isinstance(dept_data[field], int) and dept_data[field] >= 0, f"Trường '{field}' không phải số nguyên không âm"
        
        logger.info(f"✅ Thống kê bộ môn thành công! Dữ liệu: {dept_data}")

        # ----------------------------------------------------
        # TEST POSITIONS STATS
        # ----------------------------------------------------
        logger.info("🎖️ 3. Gọi API Thống kê Chức vụ (Positions Stats)")
        pos_stats_res = await ac.get("/api/v1/admin/positions/stats", headers=headers)
        assert pos_stats_res.status_code == 200, f"Lỗi positions stats: {pos_stats_res.text}"
        pos_data = pos_stats_res.json()
        
        # Verify structure
        for field in ["total", "active", "inactive"]:
            assert field in pos_data, f"Thiếu trường '{field}' trong response"
            assert isinstance(pos_data[field], int) and pos_data[field] >= 0, f"Trường '{field}' không phải số nguyên không âm"
            
        logger.info(f"✅ Thống kê chức vụ thành công! Dữ liệu: {pos_data}")

        # ----------------------------------------------------
        # TEST STAFFS STATS
        # ----------------------------------------------------
        logger.info("👨‍🏫 4. Gọi API Thống kê Giảng viên (Staffs Stats)")
        staff_stats_res = await ac.get("/api/v1/admin/staffs/stats", headers=headers)
        assert staff_stats_res.status_code == 200, f"Lỗi staffs stats: {staff_stats_res.text}"
        staff_data = staff_stats_res.json()
        
        # Verify structure
        for category in ["departments", "positions", "staffs"]:
            assert category in staff_data, f"Thiếu '{category}' trong response"
            for field in ["total", "active", "inactive"]:
                assert field in staff_data[category], f"Thiếu '{field}' trong {category}"
            
        logger.info(f"✅ Thống kê giảng viên thành công! Dữ liệu: {staff_data}")

        logger.info("🚀 TẤT CẢ CÁC BƯỚC TEST STATS API ĐÃ HOÀN THÀNH THÀNH CÔNG!")

if __name__ == "__main__":
    asyncio.run(test_stats_endpoints())
