import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from app.modules.position.models import Position


@pytest.mark.asyncio
async def test_position_crud_and_i18n(client: AsyncClient, admin_headers: dict, db_session):
    pos_id = None
    dept = None
    staff = None
    try:
        # 1. Tạo chức vụ mới
        payload = {
            "sort_order": 5,
            "is_active": True,
            "translations": {
                "vi": {
                    "name": "Trưởng bộ môn",
                    "description": "Quản lý chuyên môn của khoa"
                },
                "en": {
                    "name": "Head of Department",
                    "description": "Responsible for academic management"
                }
            }
        }
        
        res = await client.post("/api/v1/admin/positions", json=payload, headers=admin_headers)
        assert res.status_code == 201
        data = res.json()
        pos_id = data["id"]
        assert data["name"] == "Trưởng bộ môn"
        assert data["translations"]["vi"]["name"] == "Trưởng bộ môn"
        assert data["translations"]["en"]["name"] == "Head of Department"

        # 2. Update chức vụ
        update_payload = {
            "translations": {
                "vi": {
                    "name": "Trưởng bộ môn CNTT",
                    "description": "Quản lý khoa CNTT"
                }
            }
        }
        res_up = await client.put(f"/api/v1/admin/positions/{pos_id}", json=update_payload, headers=admin_headers)
        assert res_up.status_code == 200
        assert res_up.json()["name"] == "Trưởng bộ môn CNTT"

        # 3. Lấy danh sách Portal tiếng Anh
        res_portal_en = await client.get("/api/v1/portal/positions?lang=en")
        assert res_portal_en.status_code == 200
        positions_en = res_portal_en.json()
        found = [p for p in positions_en if p["id"] == pos_id]
        assert len(found) == 1
        assert found[0]["name"] == "Head of Department"
        assert "translations" not in found[0]

        # 3.5 Test stats
        res_stats = await client.get("/api/v1/admin/positions/stats", headers=admin_headers)
        assert res_stats.status_code == 200
        stats_data = res_stats.json()
        assert "total" in stats_data
        assert "active" in stats_data
        assert "inactive" in stats_data
        assert stats_data["total"] >= 1

        # 3.8 Thử xóa chức vụ khi còn giảng viên (phương án 1 - chặn xóa)
        from app.modules.department.models import Department
        from app.modules.staff.models import Staff
        
        dept = Department(is_active=True)
        db_session.add(dept)
        await db_session.commit()
        await db_session.refresh(dept)
        
        staff = Staff(
            department_id=dept.id,
            position_id=uuid.UUID(pos_id),
            full_name="Nguyễn Văn A",
            slug="nguyen-van-a-" + uuid.uuid4().hex[:8],
            is_active=True
        )
        db_session.add(staff)
        await db_session.commit()
        await db_session.refresh(staff)
        
        # Check staffs-to-delete API
        res_to_delete = await client.get(f"/api/v1/admin/positions/staffs-to-delete?position_ids={pos_id}", headers=admin_headers)
        assert res_to_delete.status_code == 200
        assert len(res_to_delete.json()) == 1
        assert res_to_delete.json()[0]["full_name"] == "Nguyễn Văn A"
        
        # Mong đợi delete thất bại với 400 Bad Request
        res_del_fail = await client.delete(f"/api/v1/admin/positions/{pos_id}", headers=admin_headers)
        assert res_del_fail.status_code == 400
        assert "Không thể xóa chức vụ này" in res_del_fail.json()["error"]["message"]
        
        # Xóa staff trước
        await db_session.delete(staff)
        await db_session.commit()
        staff = None

        # 4. Xóa chức vụ thành công
        res_del = await client.delete(f"/api/v1/admin/positions/{pos_id}", headers=admin_headers)
        assert res_del.status_code == 204

    finally:
        # Dọn dẹp dữ liệu cứng
        if staff:
            try:
                await db_session.delete(staff)
            except Exception:
                pass
        if dept:
            try:
                await db_session.delete(dept)
            except Exception:
                pass
        if pos_id:
            try:
                pos_obj = await db_session.get(Position, uuid.UUID(pos_id))
                if pos_obj:
                    await db_session.delete(pos_obj)
            except Exception:
                pass
        await db_session.commit()
