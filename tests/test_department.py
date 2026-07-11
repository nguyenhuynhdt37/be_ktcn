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
        # 0. Set up a Staff to use as head of department
        from app.modules.position.models import Position
        from app.modules.staff.models import Staff
        pos = Position(is_active=True)
        db_session.add(pos)
        await db_session.commit()
        await db_session.refresh(pos)

        # Temporary department for the dummy staff
        temp_dept = Department(
            thumbnail_object_key="temp-thumb.png",
            is_active=True
        )
        db_session.add(temp_dept)
        await db_session.commit()
        await db_session.refresh(temp_dept)

        staff = Staff(
            department_id=temp_dept.id,
            position_id=pos.id,
            full_name="Trưởng Khoa A",
            slug="truong-khoa-a-" + uuid.uuid4().hex[:8],
            is_active=True
        )
        db_session.add(staff)
        await db_session.commit()
        await db_session.refresh(staff)

        # 1. Tạo bộ môn mới cùng các trường mới
        payload = {
            "thumbnail_object_key": "dept-thumb.png",
            "logo_object_key": "dept-logo.png",
            "banner_object_key": "dept-banner.png",
            "phone": "024-123456",
            "email": "fit@university.edu.vn",
            "website": "fit.university.edu.vn",
            "office": "Room 302, Building C1",
            "sort_order": 10,
            "display_order": 1,
            "is_active": True,
            "head_staff_id": str(staff.id),
            "translations": {
                "vi": {
                    "name": "Công nghệ thông tin",
                    "description": "Khoa CNTT hàng đầu",
                    "mission": "<p>Sứ mệnh tiếng Việt</p>",
                    "vision": "<p>Tầm nhìn tiếng Việt</p>",
                    "history": "<p>Lịch sử tiếng Việt</p>",
                    "research_overview": "<p>Nghiên cứu tiếng Việt</p>",
                    "seo_title": "Khoa CNTT",
                    "seo_description": "Mô tả SEO khoa CNTT"
                },
                "en": {
                    "name": "Information Technology",
                    "description": "Leading IT department",
                    "mission": "<p>Mission in English</p>",
                    "vision": "<p>Vision in English</p>",
                    "history": "<p>History in English</p>",
                    "research_overview": "<p>Research in English</p>",
                    "seo_title": "IT Faculty",
                    "seo_description": "IT Faculty SEO Description"
                }
            }
        }
        
        res = await client.post("/api/v1/admin/departments", json=payload, headers=admin_headers)
        assert res.status_code == 201
        data = res.json()
        dept_id = data["id"]
        
        # Verify Response Fields for Admin
        assert data["name"] == "Công nghệ thông tin"
        assert data["logo_object_key"] is not None
        assert data["banner_object_key"] is not None
        assert data["display_order"] == 1
        assert data["head_staff_id"] == str(staff.id)
        assert data["translations"]["vi"]["name"] == "Công nghệ thông tin"
        assert data["translations"]["vi"]["mission"] == "<p>Sứ mệnh tiếng Việt</p>"
        assert data["translations"]["en"]["name"] == "Information Technology"
        assert data["translations"]["en"]["seo_title"] == "IT Faculty"

        # 2. Update bộ môn
        update_payload = {
            "display_order": 2,
            "translations": {
                "vi": {
                    "name": "Khoa Công nghệ thông tin",
                    "description": "Khoa CNTT uy tín",
                    "mission": "<p>Sứ mệnh mới</p>"
                }
            }
        }
        res_up = await client.put(f"/api/v1/admin/departments/{dept_id}", json=update_payload, headers=admin_headers)
        assert res_up.status_code == 200
        up_data = res_up.json()
        assert up_data["name"] == "Khoa Công nghệ thông tin"
        assert up_data["display_order"] == 2
        assert up_data["translations"]["vi"]["mission"] == "<p>Sứ mệnh mới</p>"
        # en translations should stay unchanged
        assert up_data["translations"]["en"]["name"] == "Information Technology"

        # 3. Lấy danh sách Portal tiếng Anh
        res_portal_en = await client.get("/api/v1/portal/departments?lang=en")
        assert res_portal_en.status_code == 200
        depts_en = res_portal_en.json()
        found = [d for d in depts_en if d["id"] == dept_id]
        assert len(found) == 1
        assert found[0]["name"] == "Information Technology"
        assert found[0]["mission"] == "<p>Mission in English</p>"
        assert found[0]["display_order"] == 2
        assert found[0]["logo_object_key"] is not None
        assert found[0]["banner_object_key"] is not None
        assert "translations" not in found[0]

        # 4. Kiểm tra Validation cho head_staff_id không tồn tại
        bad_payload = payload.copy()
        bad_payload["head_staff_id"] = str(uuid.uuid4())
        res_bad = await client.post("/api/v1/admin/departments", json=bad_payload, headers=admin_headers)
        assert res_bad.status_code == 400
        assert "Không tìm thấy giảng viên" in res_bad.json()["error"]["message"]

        # 4.5. Test Department SEO Analyze Endpoint
        seo_req_payload = {
            "name": "Khoa Công nghệ thông tin",
            "description": "Khoa CNTT uy tín đào tạo hàng đầu Việt Nam.",
            "mission": "<h3>Sứ mệnh</h3><p>Đào tạo nguồn nhân lực CNTT chất lượng cao.</p>",
            "vision": "<h3>Tầm nhìn</h3><p>Trở thành khoa nghiên cứu hàng đầu.</p>",
            "history": "<h3>Lịch sử</h3><p>Thành lập năm 2002.</p>",
            "research_overview": "<h3>Nghiên cứu</h3><p>Tập trung AI, IoT.</p>",
            "seo_title": "Khoa CNTT - Đại học Công nghệ",
            "seo_description": "Mô tả SEO cho Khoa CNTT với từ khóa chính.",
            "focus_keyword": "Công nghệ thông tin",
            "thumbnail_object_key": "thumb.png",
            "logo_object_key": "logo.png",
            "banner_object_key": "banner.png",
            "slug": "khoa-cong-nghe-thong-tin",
            "lang": "vi"
        }
        res_seo = await client.post(f"/api/v1/admin/departments/{dept_id}/seo/analyze", json=seo_req_payload, headers=admin_headers)
        assert res_seo.status_code == 200
        seo_data = res_seo.json()
        assert "score" in seo_data
        assert "status" in seo_data
        assert "issues" in seo_data
        assert "google_preview" in seo_data
        assert "suggestions" in seo_data
        assert "generated_seo_title" in seo_data
        assert "generated_meta_description" in seo_data

        # 5. Xóa bộ môn
        res_del = await client.delete(f"/api/v1/admin/departments/{dept_id}", headers=admin_headers)
        assert res_del.status_code == 204

    finally:
        # Dọn dẹp dữ liệu
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
        try:
            temp_dept_obj = await db_session.get(Department, temp_dept.id)
            if temp_dept_obj:
                await db_session.delete(temp_dept_obj)
        except Exception:
            pass
        await db_session.commit()

