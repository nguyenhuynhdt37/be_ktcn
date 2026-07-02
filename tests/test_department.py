import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from app.modules.department.models import Department, DepartmentTranslation


@pytest.mark.asyncio
async def test_department_crud_and_i18n(client: AsyncClient, admin_headers: dict, db_session):
    dept_id = None
    pos = None
    staff = None
    try:
        # 1. Tạo bộ môn mới
        payload = {
            "thumbnail_object_key": "dept-thumb.png",
            "phone": "024-123456",
            "email": "fit@university.edu.vn",
            "website": "fit.university.edu.vn",
            "office": "Room 302, Building C1",
            "sort_order": 10,
            "is_active": True,
            "translations": {
                "vi": {
                    "name": "Công nghệ thông tin",
                    "description": "Khoa CNTT hàng đầu"
                },
                "en": {
                    "name": "Information Technology",
                    "description": "Leading IT department"
                }
            }
        }
        
        res = await client.post("/api/v1/admin/departments", json=payload, headers=admin_headers)
        assert res.status_code == 201
        data = res.json()
        dept_id = data["id"]
        assert data["name"] == "Công nghệ thông tin"
        assert data["translations"]["vi"]["name"] == "Công nghệ thông tin"
        assert data["translations"]["en"]["name"] == "Information Technology"
        assert data["translations"]["en"]["slug"].startswith("information-technology")

        # 2. Update bộ môn
        update_payload = {
            "translations": {
                "vi": {
                    "name": "Khoa Công nghệ thông tin",
                    "description": "Khoa CNTT uy tín"
                }
            }
        }
        res_up = await client.put(f"/api/v1/admin/departments/{dept_id}", json=update_payload, headers=admin_headers)
        assert res_up.status_code == 200
        assert res_up.json()["name"] == "Khoa Công nghệ thông tin"

        # 3. Lấy danh sách Portal tiếng Anh
        res_portal_en = await client.get("/api/v1/portal/departments?lang=en")
        assert res_portal_en.status_code == 200
        depts_en = res_portal_en.json()
        found = [d for d in depts_en if d["id"] == dept_id]
        assert len(found) == 1
        assert found[0]["name"] == "Information Technology"
        # Portal không được chứa metadata audit hay translations map
        assert "translations" not in found[0]

        # 3.5 Test stats
        res_stats = await client.get("/api/v1/admin/departments/stats", headers=admin_headers)
        assert res_stats.status_code == 200
        stats_data = res_stats.json()
        assert "total" in stats_data
        assert "active" in stats_data
        assert "inactive" in stats_data
        assert stats_data["total"] >= 1

        # 3.8 Tạo staff thuộc department
        from app.modules.position.models import Position
        from app.modules.staff.models import Staff
        pos = Position(is_active=True)
        db_session.add(pos)
        await db_session.commit()
        await db_session.refresh(pos)

        staff = Staff(
            department_id=uuid.UUID(dept_id),
            position_id=pos.id,
            full_name="Nguyễn Văn A",
            slug="nguyen-van-a-" + uuid.uuid4().hex[:8],
            is_active=True
        )
        db_session.add(staff)
        await db_session.commit()
        await db_session.refresh(staff)

        # 4. Xóa bộ môn
        res_del = await client.delete(f"/api/v1/admin/departments/{dept_id}", headers=admin_headers)
        assert res_del.status_code == 204

        # Kiểm tra staff thuộc bộ môn đã bị xóa mềm chưa
        await db_session.refresh(staff)
        assert staff.deleted_at is not None

    finally:
        # Dọn dẹp dữ liệu cứng
        if staff:
            try:
                await db_session.delete(staff)
            except Exception:
                pass
        if pos:
            try:
                await db_session.delete(pos)
            except Exception:
                pass
        if dept_id:
            try:
                dept_obj = await db_session.get(Department, uuid.UUID(dept_id))
                if dept_obj:
                    await db_session.delete(dept_obj)
            except Exception:
                pass
        await db_session.commit()
