import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from app.modules.department.models import Department
from app.modules.position.models import Position
from app.modules.staff.models import Staff


@pytest.mark.asyncio
async def test_staff_crud_and_i18n(client: AsyncClient, admin_headers: dict, db_session):
    dept = None
    pos = None
    staff_id = None
    try:
        # 1. Tạo mock Department và Position trước
        dept = Department(is_active=True)
        db_session.add(dept)
        pos = Position(is_active=True)
        db_session.add(pos)
        await db_session.commit()
        await db_session.refresh(dept)
        await db_session.refresh(pos)

        # Thêm translation cho Department và Position để test load quan hệ dịch
        from app.modules.department.models import DepartmentTranslation
        from app.modules.position.models import PositionTranslation
        from app.modules.language.models import Language
        from app.modules.academic_title.models import AcademicTitle
        from app.modules.degree.models import Degree

        vi_lang = (await db_session.execute(select(Language).where(Language.code == "vi"))).scalar()
        en_lang = (await db_session.execute(select(Language).where(Language.code == "en"))).scalar()

        slug_vi = f"khoa-cntt-{uuid.uuid4().hex[:8]}"
        slug_en = f"faculty-of-it-{uuid.uuid4().hex[:8]}"
        dt = DepartmentTranslation(department_id=dept.id, language_id=vi_lang.id, name="Khoa CNTT", slug=slug_vi)
        dt_en = DepartmentTranslation(department_id=dept.id, language_id=en_lang.id, name="Faculty of IT", slug=slug_en)
        db_session.add_all([dt, dt_en])

        pt = PositionTranslation(position_id=pos.id, language_id=vi_lang.id, name="Giảng viên")
        pt_en = PositionTranslation(position_id=pos.id, language_id=en_lang.id, name="Lecturer")
        db_session.add_all([pt, pt_en])
        await db_session.commit()

        # Lấy PGS (Associate Professor) và TS (Doctor of Philosophy) đã seed
        title_res = await db_session.execute(select(AcademicTitle))
        pgs_title = None
        for t in title_res.scalars().all():
            for trans in t.translations:
                if trans.language.code == "en" and trans.name == "Associate Professor":
                    pgs_title = t
                    break
            if pgs_title:
                break

        degree_res = await db_session.execute(select(Degree))
        ts_degree = None
        for d in degree_res.scalars().all():
            for trans in d.translations:
                if trans.language.code == "en" and trans.name == "Doctor of Philosophy":
                    ts_degree = d
                    break
            if ts_degree:
                break

        # 2. Tạo giảng viên mới
        payload = {
            "department_id": str(dept.id),
            "position_id": str(pos.id),
            "academic_title_id": str(pgs_title.id) if pgs_title else None,
            "degree_id": str(ts_degree.id) if ts_degree else None,
            "full_name": "Nguyễn Văn A",
            "english_name": "Nguyen Van A",
            "avatar_object_key": "avatar.png",
            "email": "nva@university.edu.vn",
            "phone": "0987654321",
            "website": "nva.edu.vn",
            "office": "Room 501",
            "sort_order": 1,
            "is_active": True,
            "translations": {
                "vi": {
                    "biography": "Lý lịch khoa học",
                    "research_interests": "Trí tuệ nhân tạo"
                },
                "en": {
                    "biography": "Scientific Biography",
                    "research_interests": "Artificial Intelligence"
                }
            }
        }
        
        res = await client.post("/api/v1/admin/staffs", json=payload, headers=admin_headers)
        assert res.status_code == 201
        data = res.json()
        staff_id = data["id"]
        assert data["full_name"] == "Nguyễn Văn A"
        assert data["academic_title_id"] == (str(pgs_title.id) if pgs_title else None)
        assert data["degree_id"] == (str(ts_degree.id) if ts_degree else None)
        assert data["academic_title"] == "Phó giáo sư"
        assert data["degree"] == "Tiến sĩ"
        assert data["slug"].startswith("nguyen-van-a")

        # Lấy GS (Professor) và TSKH (Doctor of Science) để update
        gs_title = None
        title_res = await db_session.execute(select(AcademicTitle))
        for t in title_res.scalars().all():
            for trans in t.translations:
                if trans.language.code == "en" and trans.name == "Professor":
                    gs_title = t
                    break
            if gs_title:
                break

        tskh_degree = None
        degree_res = await db_session.execute(select(Degree))
        for d in degree_res.scalars().all():
            for trans in d.translations:
                if trans.language.code == "en" and trans.name == "Doctor of Science":
                    tskh_degree = d
                    break
            if tskh_degree:
                break

        # 3. Update giảng viên
        update_payload = {
            "academic_title_id": str(gs_title.id) if gs_title else None,
            "degree_id": str(tskh_degree.id) if tskh_degree else None,
            "translations": {
                "vi": {
                    "biography": "Lý lịch khoa học chi tiết"
                }
            }
        }
        res_up = await client.put(f"/api/v1/admin/staffs/{staff_id}", json=update_payload, headers=admin_headers)
        assert res_up.status_code == 200
        assert res_up.json()["academic_title"] == "Giáo sư"
        assert res_up.json()["degree"] == "Tiến sĩ khoa học"

        # 4. Lấy danh sách Portal tiếng Anh
        res_portal_en = await client.get("/api/v1/portal/staffs?lang=en")
        assert res_portal_en.status_code == 200
        staffs_en = res_portal_en.json()
        found = [s for s in staffs_en if s["id"] == staff_id]
        assert len(found) == 1
        assert found[0]["academic_title"] == "Professor"
        assert found[0]["degree"] == "Doctor of Science"
        # Kiểm tra load quan hệ Department và Position đã được dịch tự động
        assert found[0]["department"]["name"] == "Faculty of IT"
        assert found[0]["position"]["name"] == "Lecturer"
        assert "translations" not in found[0]

        # 4.5 Lấy thống kê của 3 bảng qua API Admin
        res_stats = await client.get("/api/v1/admin/staffs/stats", headers=admin_headers)
        assert res_stats.status_code == 200
        stats_data = res_stats.json()
        assert "departments" in stats_data
        assert "positions" in stats_data
        assert "staffs" in stats_data
        assert stats_data["departments"]["total"] >= 1
        assert stats_data["positions"]["total"] >= 1
        assert stats_data["staffs"]["total"] >= 1

        # 5. Xóa giảng viên
        res_del = await client.delete(f"/api/v1/admin/staffs/{staff_id}", headers=admin_headers)
        assert res_del.status_code == 204

    finally:
        # Dọn dẹp dữ liệu cứng
        if staff_id:
            try:
                st = await db_session.get(Staff, uuid.UUID(staff_id))
                if st:
                    await db_session.delete(st)
            except Exception:
                pass
        if dept:
            try:
                await db_session.delete(dept)
            except Exception:
                pass
        if pos:
            try:
                await db_session.delete(pos)
            except Exception:
                pass
        await db_session.commit()
