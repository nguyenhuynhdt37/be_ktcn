import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.modules.department.models import Department
from app.modules.position.models import Position
from app.modules.staff.models import Staff
from app.modules.language.models import Language


@pytest.mark.asyncio
async def test_department_sort_order_reordering(client: AsyncClient, admin_headers: dict, db_session):
    # 1. Lấy vi_lang và en_lang
    vi_lang = (await db_session.execute(select(Language).where(Language.code == "vi"))).scalar()
    en_lang = (await db_session.execute(select(Language).where(Language.code == "en"))).scalar()

    dept_a_id = None
    dept_b_id = None
    dept_c_id = None

    try:
        # 2. Tạo 3 Department với sort_order lần lượt là 1, 2, 3
        # Dept A
        res_a = await client.post("/api/v1/admin/departments", json={
            "thumbnail_object_key": "a.png",
            "sort_order": 1,
            "is_active": True,
            "translations": {
                "vi": {"name": "Dept A", "description": "A", "slug": "dept-a"},
                "en": {"name": "Dept A Eng", "description": "A Eng", "slug": "dept-a-eng"}
            }
        }, headers=admin_headers)
        assert res_a.status_code == 201
        dept_a_id = res_a.json()["id"]

        # Dept B
        res_b = await client.post("/api/v1/admin/departments", json={
            "thumbnail_object_key": "b.png",
            "sort_order": 2,
            "is_active": True,
            "translations": {
                "vi": {"name": "Dept B", "description": "B", "slug": "dept-b"},
                "en": {"name": "Dept B Eng", "description": "B Eng", "slug": "dept-b-eng"}
            }
        }, headers=admin_headers)
        assert res_b.status_code == 201
        dept_b_id = res_b.json()["id"]

        # Dept C
        res_c = await client.post("/api/v1/admin/departments", json={
            "thumbnail_object_key": "c.png",
            "sort_order": 3,
            "is_active": True,
            "translations": {
                "vi": {"name": "Dept C", "description": "C", "slug": "dept-c"},
                "en": {"name": "Dept C Eng", "description": "C Eng", "slug": "dept-c-eng"}
            }
        }, headers=admin_headers)
        assert res_c.status_code == 201
        dept_c_id = res_c.json()["id"]

        # 3. Cập nhật Dept C lên sort_order = 1 (trước Dept A)
        # Hệ thống cần tự động đẩy Dept A lên 2, Dept B lên 3, Dept C thành 1
        res_up = await client.put(f"/api/v1/admin/departments/{dept_c_id}", json={
            "sort_order": 1
        }, headers=admin_headers)
        assert res_up.status_code == 200

        # Lấy lại danh sách và kiểm tra sort_order
        res_list = await client.get("/api/v1/admin/departments", headers=admin_headers)
        assert res_list.status_code == 200
        items = res_list.json()["items"]
        
        # Tìm thứ tự của 3 Dept vừa tạo
        dict_orders = {item["id"]: item["sort_order"] for item in items}
        assert dict_orders[dept_c_id] == 1
        assert dict_orders[dept_a_id] == 2
        assert dict_orders[dept_b_id] == 3

    finally:
        # Dọn dẹp dữ liệu cứng
        for d_id in [dept_a_id, dept_b_id, dept_c_id]:
            if d_id:
                try:
                    d_obj = await db_session.get(Department, uuid.UUID(d_id))
                    if d_obj:
                        await db_session.delete(d_obj)
                except Exception:
                    pass
        await db_session.commit()
