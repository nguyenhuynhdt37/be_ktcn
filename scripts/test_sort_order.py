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

async def test_sort_order_flow():
    username, password = await setup_test_user()
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        logger.info("🔑 1. Đăng nhập lấy Token")
        login_res = await ac.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("✅ Đăng nhập thành công!")

        # ----------------------------------------------------
        # TEST DEPARTMENTS SORT ORDER
        # ----------------------------------------------------
        logger.info("🏢 TEST DEPARTMENTS SORT ORDER...")
        
        # 0. Lấy số lượng bộ môn hiện có trước khi test
        init_list_res = await ac.get("/api/v1/departments?page_size=100")
        assert init_list_res.status_code == 200
        k = init_list_res.json()["total_items"]
        logger.info(f"📊 Số lượng bộ môn hiện tại trong DB: {k}")

        # 1. Tạo mới 3 bộ môn test ở cuối danh sách (truyền sort_order = 999)
        suffix = uuid.uuid4().hex[:6]
        
        # Bộ môn A (nhập 999 -> validated = k)
        res_a = await ac.post("/api/v1/departments", json={
            "name": f"Bộ môn Test A {suffix}",
            "sort_order": 999,
            "is_active": True
        }, headers=headers)
        assert res_a.status_code == 201
        id_a = res_a.json()["id"]
        assert res_a.json()["sort_order"] == k
        
        # Bộ môn B (nhập 999 -> validated = k + 1)
        res_b = await ac.post("/api/v1/departments", json={
            "name": f"Bộ môn Test B {suffix}",
            "sort_order": 999,
            "is_active": True
        }, headers=headers)
        assert res_b.status_code == 201
        id_b = res_b.json()["id"]
        assert res_b.json()["sort_order"] == k + 1
        
        # Bộ môn C (nhập 999 -> validated = k + 2)
        res_c = await ac.post("/api/v1/departments", json={
            "name": f"Bộ môn Test C {suffix}",
            "sort_order": 999,
            "is_active": True
        }, headers=headers)
        assert res_c.status_code == 201
        id_c = res_c.json()["id"]
        assert res_c.json()["sort_order"] == k + 2
        logger.info(f"✅ Tạo mới 3 bộ môn ở cuối thành công: A:{k}, B:{k+1}, C:{k+2}")

        # Bộ môn D (chèn ở giữa: sort_order = k + 1)
        res_d = await ac.post("/api/v1/departments", json={
            "name": f"Bộ môn Test D {suffix}",
            "sort_order": k + 1,
            "is_active": True
        }, headers=headers)
        assert res_d.status_code == 201
        id_d = res_d.json()["id"]
        assert res_d.json()["sort_order"] == k + 1
        
        # Lấy lại danh sách kiểm tra xem B, C có bị đẩy lên không
        logger.info("🔍 Kiểm tra dọn hàng khi chèn mới...")
        list_res = await ac.get("/api/v1/departments?page_size=100&sort_by=sort_order&order=asc")
        assert list_res.status_code == 200
        items = [x for x in list_res.json()["items"] if suffix in x["name"]]
        assert len(items) == 4
        # Phải là A: k, D: k+1, B: k+2, C: k+3
        mapping = {x["id"]: x["sort_order"] for x in items}
        logger.info(f"📊 Mapping thực tế: {mapping}")
        logger.info(f"📊 Chi tiết items: {items}")
        assert mapping[id_a] == k
        assert mapping[id_d] == k + 1
        assert mapping[id_b] == k + 2
        assert mapping[id_c] == k + 3
        logger.info(f"✅ Dịch hàng thành công! Thứ tự đúng: A:{k}, D:{k+1}, B:{k+2}, C:{k+3}")

        # 2. Di chuyển thứ tự (update)
        # Trường hợp 1: Di chuyển D (k+1 -> k+3) (xuống cuối nhóm test)
        logger.info(f"🔄 Di chuyển D từ {k+1} -> {k+3} (xuống cuối)")
        update_res1 = await ac.put(f"/api/v1/departments/{id_d}", json={"sort_order": k + 3}, headers=headers)
        assert update_res1.status_code == 200
        assert update_res1.json()["sort_order"] == k + 3
        
        # Lấy lại kiểm tra
        list_res = await ac.get("/api/v1/departments?page_size=100&sort_by=sort_order&order=asc")
        items = [x for x in list_res.json()["items"] if suffix in x["name"]]
        mapping = {x["id"]: x["sort_order"] for x in items}
        # Kỳ vọng: A: k, B: k+1, C: k+2, D: k+3
        assert mapping[id_a] == k
        assert mapping[id_b] == k + 1
        assert mapping[id_c] == k + 2
        assert mapping[id_d] == k + 3
        logger.info(f"✅ Di chuyển xuống cuối thành công! Thứ tự đúng: A:{k}, B:{k+1}, C:{k+2}, D:{k+3}")

        # Trường hợp 2: Di chuyển C (k+2 -> k) (lên đầu nhóm test)
        logger.info(f"🔄 Di chuyển C từ {k+2} -> {k} (lên đầu)")
        update_res2 = await ac.put(f"/api/v1/departments/{id_c}", json={"sort_order": k}, headers=headers)
        assert update_res2.status_code == 200
        assert update_res2.json()["sort_order"] == k

        # Lấy lại kiểm tra
        list_res = await ac.get("/api/v1/departments?page_size=100&sort_by=sort_order&order=asc")
        items = [x for x in list_res.json()["items"] if suffix in x["name"]]
        mapping = {x["id"]: x["sort_order"] for x in items}
        # Kỳ vọng: C: k, A: k+1, B: k+2, D: k+3
        assert mapping[id_c] == k
        assert mapping[id_a] == k + 1
        assert mapping[id_b] == k + 2
        assert mapping[id_d] == k + 3
        logger.info(f"✅ Di chuyển lên đầu thành công! Thứ tự đúng: C:{k}, A:{k+1}, B:{k+2}, D:{k+3}")

        # 3. Xóa bộ môn
        # Xóa B ở vị trí k+2
        logger.info(f"🗑️ Xóa bộ môn B ở vị trí {k+2}")
        del_res = await ac.delete(f"/api/v1/departments/{id_b}", headers=headers)
        assert del_res.status_code == 204
        
        # Lấy lại kiểm tra
        list_res = await ac.get("/api/v1/departments?page_size=100&sort_by=sort_order&order=asc")
        items = [x for x in list_res.json()["items"] if suffix in x["name"]]
        assert len(items) == 3
        mapping = {x["id"]: x["sort_order"] for x in items}
        # Kỳ vọng: C: k, A: k+1, D: k+2 (D giảm từ k+3 về k+2)
        assert mapping[id_c] == k
        assert mapping[id_a] == k + 1
        assert mapping[id_d] == k + 2
        logger.info(f"✅ Xóa và dồn hàng thành công! Thứ tự đúng: C:{k}, A:{k+1}, D:{k+2}")

        # Dọn dẹp các bộ môn test
        logger.info("🧹 Dọn dẹp dữ liệu test departments")
        for temp_id in [id_a, id_c, id_d]:
            await ac.delete(f"/api/v1/departments/{temp_id}", headers=headers)
        logger.info("✅ Dọn dẹp xong!")

if __name__ == "__main__":
    asyncio.run(test_sort_order_flow())
