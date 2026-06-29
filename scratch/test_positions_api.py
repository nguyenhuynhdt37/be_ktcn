import asyncio
import sys
import uuid
from typing import Any

# Đảm bảo import được thư mục gốc của dự án
sys.path.append("/Users/huynh/codes/be")

import httpx
from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.core.database import SessionLocal
from app.modules.faculty_staff.models import Department, Position, Staff
from app.modules.auth.models import User
from sqlalchemy import select

# ID người dùng test cố định để mock và tạo trong database
TEST_USER_ID = uuid.UUID("99999999-9999-9999-9999-999999999999")

# 1. Ghi đè dependency get_current_user để giả lập đã đăng nhập với user test hợp lệ
mock_user = UserResponse(
    id=TEST_USER_ID,
    username="admin_test_user",
    email="admin_test_user@test.com",
    is_active=True
)

async def override_get_current_user() -> UserResponse:
    return mock_user

app.dependency_overrides[get_current_user] = override_get_current_user


async def setup_clean_db():
    """Dọn dẹp các bảng positions, staffs, depts và tạo user test hợp lệ trong bảng users."""
    async with SessionLocal() as session:
        # Xóa staffs
        staffs = await session.execute(select(Staff))
        for s in staffs.scalars():
            await session.delete(s)
        
        # Xóa depts
        depts = await session.execute(select(Department))
        for d in depts.scalars():
            await session.delete(d)

        # Xóa positions
        positions = await session.execute(select(Position))
        for p in positions.scalars():
            await session.delete(p)

        # Kiểm tra và xóa user test cũ nếu tồn tại
        stmt = select(User).where(User.id == TEST_USER_ID)
        old_user = (await session.execute(stmt)).scalar_one_or_none()
        if old_user:
            await session.delete(old_user)
            await session.flush()

        # Tạo user test thật trong DB để không vi phạm khóa ngoại audit_logs
        test_user = User(
            id=TEST_USER_ID,
            username="admin_test_user",
            email="admin_test_user@test.com",
            password_hash="mocked_password_hash_123",
            full_name="Admin Test User",
            is_active=True
        )
        session.add(test_user)
        await session.commit()


async def cleanup_db():
    """Dọn dẹp sạch sẽ database sau khi chạy test bao gồm cả user test."""
    async with SessionLocal() as session:
        staffs = await session.execute(select(Staff))
        for s in staffs.scalars():
            await session.delete(s)
        
        depts = await session.execute(select(Department))
        for d in depts.scalars():
            await session.delete(d)

        positions = await session.execute(select(Position))
        for p in positions.scalars():
            await session.delete(p)

        # Xóa user test
        u = await session.get(User, TEST_USER_ID)
        if u:
            await session.delete(u)

        await session.commit()


async def run_api_tests():
    print("=== BẮT ĐẦU KIỂM THỬ API MODULE POSITIONS (ASYNC) ===")

    # Dọn dẹp DB trước khi test
    await setup_clean_db()
    print("1. Đã dọn dẹp sạch cơ sở dữ liệu và tạo user test.")

    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        # 2. Test POST /positions - Tạo mới thành công và kiểm tra trim khoảng trắng
        print("2. Test POST /positions (Tạo mới)...")
        payload = {
            "name": "   Trưởng bộ môn   ",
            "english_name": "  Head of Department  ",
            "description": "Quản lý hoạt động giảng dạy và nghiên cứu khoa học.",
            "sort_order": 5,
            "is_active": True
        }
        response = await ac.post("/api/v1/positions", json=payload)
        assert response.status_code == 201, f"Tạo thất bại: {response.text}"
        data = response.json()
        assert data["name"] == "Trưởng bộ môn", "Lỗi: Không tự động trim name"
        assert data["english_name"] == "Head of Department", "Lỗi: Không tự động trim english_name"
        assert data["sort_order"] == 5
        assert data["is_active"] is True
        assert data["staff_count"] == 0
        pos_id = data["id"]
        print(f"SUCCESS: Đã tạo chức vụ '{data['name']}' thành công (ID: {pos_id})")

        # 3. Test POST /positions - Chặn trùng tên
        print("3. Test check trùng tên...")
        response = await ac.post("/api/v1/positions", json={
            "name": "Trưởng bộ môn",
            "sort_order": 1
        })
        assert response.status_code == 409, f"Trùng tên mà vẫn tạo được: {response.status_code}"
        print("SUCCESS: Đã chặn trùng tên thành công (trả về 409 Conflict).")

        # 4. Test Validation sort_order >= 0
        print("4. Test check validation sort_order < 0...")
        response = await ac.post("/api/v1/positions", json={
            "name": "Giảng viên",
            "sort_order": -1
        })
        assert response.status_code == 422, f"Không validate được sort_order < 0: {response.status_code}"
        print("SUCCESS: Đã chặn thành công sort_order < 0 (trả về 422 Unprocessable Entity).")

        # Tạo thêm một vị trí thứ 2 để test list/sort
        payload_2 = {
            "name": "Giảng viên",
            "english_name": "Lecturer",
            "sort_order": 10,
            "is_active": True
        }
        response = await ac.post("/api/v1/positions", json=payload_2)
        assert response.status_code == 201
        pos_2_id = response.json()["id"]
        print("Đã tạo thêm chức vụ thứ 2: 'Giảng viên'.")

        # 5. Test GET /positions - Lấy danh sách
        print("5. Test GET /positions (Danh sách)...")
        # Test sort_order ASC (mặc định)
        response = await ac.get("/api/v1/positions")
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 2
        assert items[0]["id"] == pos_id  # sort_order 5 < 10
        assert items[1]["id"] == pos_2_id

        # Test search
        response = await ac.get("/api/v1/positions?search=Lecturer")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == pos_2_id

        # Test filter is_active
        response = await ac.get("/api/v1/positions?is_active=true")
        assert len(response.json()) == 2

        print("SUCCESS: Các chức năng search, sort, filter của danh sách chạy đúng.")

        # 6. Test GET /positions/{id} - Lấy chi tiết
        print("6. Test GET /positions/{id} (Chi tiết)...")
        response = await ac.get(f"/api/v1/positions/{pos_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Trưởng bộ môn"
        print("SUCCESS: Lấy chi tiết chức vụ thành công.")

        # 7. Test PUT /positions/{id} - Cập nhật
        print("7. Test PUT /positions/{id} (Cập nhật)...")
        response = await ac.put(f"/api/v1/positions/{pos_id}", json={
            "name": "Trưởng bộ môn CNTT",
            "english_name": "Head of IT Department",
            "sort_order": 3
        })
        assert response.status_code == 200
        assert response.json()["name"] == "Trưởng bộ môn CNTT"
        assert response.json()["english_name"] == "Head of IT Department"
        assert response.json()["sort_order"] == 3
        print("SUCCESS: Cập nhật thông tin thành công.")

        # 8. Test PATCH /positions/{id}/status - Đổi trạng thái
        print("8. Test PATCH /positions/{id}/status (Đổi trạng thái)...")
        response = await ac.patch(f"/api/v1/positions/{pos_id}/status", json={"is_active": False})
        assert response.status_code == 200
        assert response.json()["is_active"] is False
        print("SUCCESS: Đổi trạng thái hoạt động thành công.")

        # 9. Test DELETE /positions/{id} - Ràng buộc giảng viên và Xóa mềm
        print("9. Test DELETE /positions/{id} (Ràng buộc & Xóa mềm)...")
        
        # Tạo một bộ môn giả và một giảng viên giả
        async def create_dummy_staff(pos_id_uuid, pos_2_id_uuid):
            async with SessionLocal() as session:
                # Tạo bộ môn
                d = Department(name="Công nghệ phần mềm", slug="cnpm")
                session.add(d)
                await session.commit()
                await session.refresh(d)
                
                # Tạo giảng viên
                s = Staff(
                    department_id=d.id,
                    position_id=pos_id_uuid,
                    full_name="Nguyễn Văn B",
                    slug="nguyen-van-b",
                    is_active=True
                )
                session.add(s)
                await session.commit()
                return s.id, d.id
                
        dummy_staff_id, dummy_dept_id = await create_dummy_staff(uuid.UUID(pos_id), uuid.UUID(pos_2_id))
        print("Đã tạo giảng viên giả liên kết với chức vụ.")

        # Thử delete chức vụ khi đang còn giảng viên
        response = await ac.delete(f"/api/v1/positions/{pos_id}")
        assert response.status_code == 400, f"Xóa được vị trí đang có giảng viên: {response.status_code}"
        print("SUCCESS: Chặn xóa vị trí (RESTRICT) khi đang có giảng viên thành công.")

        # Xóa giảng viên giả đi để có thể xóa chức vụ
        async def delete_dummy_staff(staff_id_uuid, dept_id_uuid):
            async with SessionLocal() as session:
                s = await session.get(Staff, staff_id_uuid)
                if s:
                    await session.delete(s)
                d = await session.get(Department, dept_id_uuid)
                if d:
                    await session.delete(d)
                await session.commit()
                
        await delete_dummy_staff(dummy_staff_id, dummy_dept_id)
        print("Đã dọn dẹp giảng viên giả.")

        # Tiến hành xóa mềm chức vụ
        response = await ac.delete(f"/api/v1/positions/{pos_id}")
        assert response.status_code == 204
        print("SUCCESS: Xóa mềm chức vụ thành công (trả về 204).")

        # Kiểm tra xem chức vụ đã bị xóa mềm có xuất hiện trong danh sách nữa không
        response = await ac.get("/api/v1/positions")
        assert len(response.json()) == 1, "Chức vụ đã xóa vẫn nằm trong danh sách"
        
        # Thử tạo lại một chức vụ mới trùng tên với chức vụ vừa bị xóa mềm
        # Phải tạo được vì bản ghi cũ đã bị xóa mềm
        response = await ac.post("/api/v1/positions", json={
            "name": "Trưởng bộ môn CNTT",
            "sort_order": 1
        })
        assert response.status_code == 201, f"Không tạo lại được trùng tên với chức vụ đã xóa: {response.text}"
        print("SUCCESS: Cho phép tạo trùng tên với chức vụ đã bị xóa mềm thành công.")

    # Dọn dẹp sạch DB sau test
    await cleanup_db()
    print("10. Đã dọn dẹp sạch cơ sở dữ liệu sau kiểm thử.")
    print("=== TẤT CẢ KIỂM THỬ API THÀNH CÔNG ===")


if __name__ == "__main__":
    asyncio.run(run_api_tests())
