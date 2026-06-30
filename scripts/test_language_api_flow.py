import asyncio
import sys
from loguru import logger
import httpx

from app.core.config import settings

# Cấu hình logger
logger.remove()
logger.add(sys.stderr, level="INFO")

# Thông tin tài khoản admin test
ADMIN_CREDENTIALS = {
    "username": "admin_api_test",
    "password": "admin_api_password"
}

async def test_api_flow():
    # Sử dụng AsyncClient của httpx kết nối trực tiếp app FastAPI thông qua ASGI
    # Tránh việc phải chạy server uvicorn thực tế khi chạy test script
    from app.main import app
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        logger.info("🔑 1. Đăng nhập tài khoản Admin lấy Token")
        login_payload = {
            "username": "superadmin",
            "password": "Password@123"
        }
        login_res = await ac.post("/api/v1/auth/login", json=login_payload)
            
        assert login_res.status_code == 200, f"Đăng nhập thất bại: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("✅ Đăng nhập thành công!")

        logger.info("📋 2. Lấy danh sách Ngôn ngữ (Admin)")
        list_res = await ac.get("/api/v1/languages", headers=headers)
        assert list_res.status_code == 200
        languages = list_res.json()
        assert len(languages) == 3, f"Số lượng ngôn ngữ hệ thống không chính xác: {len(languages)}"
        logger.info(f"✅ Lấy danh sách thành công, tổng số ngôn ngữ: {len(languages)}")
        
        vi_lang = next(item for item in languages if item["code"] == "vi")
        en_lang = next(item for item in languages if item["code"] == "en")
        lo_lang = next(item for item in languages if item["code"] == "lo")

        logger.info("🔍 3. Lấy chi tiết Ngôn ngữ (en)")
        get_res = await ac.get(f"/api/v1/languages/{en_lang['id']}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["code"] == "en"
        logger.info("✅ Lấy chi tiết thành công!")

        logger.info("📐 4. Reorder Ngôn ngữ (Kéo thả)")
        reorder_payload = {
            "items": [
                {"id": vi_lang["id"], "sort_order": 10},
                {"id": en_lang["id"], "sort_order": 20},
                {"id": lo_lang["id"], "sort_order": 30}
            ]
        }
        reorder_res = await ac.put("/api/v1/languages/reorder", json=reorder_payload, headers=headers)
        assert reorder_res.status_code == 200
        assert reorder_res.json()["success"] is True
        logger.info("✅ Reorder ngôn ngữ thành công!")

        logger.info("🔄 5. Cập nhật Trạng thái hoạt động (Disable/Enable en)")
        # Disable
        disable_res = await ac.patch(f"/api/v1/languages/{en_lang['id']}/disable", headers=headers)
        assert disable_res.status_code == 200
        assert disable_res.json()["is_active"] is False
        logger.info("✅ Vô hiệu hóa ngôn ngữ en thành công!")

        # Enable
        enable_res = await ac.patch(f"/api/v1/languages/{en_lang['id']}/enable", headers=headers)
        assert enable_res.status_code == 200
        assert enable_res.json()["is_active"] is True
        logger.info("✅ Kích hoạt lại ngôn ngữ en thành công!")

        logger.info("👑 6. Thiết lập làm ngôn ngữ mặc định (en)")
        default_res = await ac.patch(f"/api/v1/languages/{en_lang['id']}/set-default", headers=headers)
        assert default_res.status_code == 200
        assert default_res.json()["is_default"] is True
        logger.info("✅ Thiết lập làm mặc định thành công!")

        logger.info("⚠️ 7. Kiểm tra validation: Không được disable ngôn ngữ mặc định mới (en)")
        dis_fail_res = await ac.patch(f"/api/v1/languages/{en_lang['id']}/disable", headers=headers)
        assert dis_fail_res.status_code == 400
        logger.info("✅ Ngăn chặn disable mặc định chính xác!")

        logger.info("🌐 8. Lấy danh sách Public Portal API (Xác thực schema rút gọn)")
        portal_res = await ac.get("/api/v1/portal/languages")
        assert portal_res.status_code == 200
        portal_list = portal_res.json()
        assert len(portal_list) >= 1
        
        vi_portal = next(item for item in portal_list if item["code"] == "vi")
        assert "is_active" not in vi_portal
        assert "sort_order" not in vi_portal
        assert "deleted_at" not in vi_portal
        assert "flag_id" in vi_portal
        assert "flag_url" in vi_portal
        logger.info("✅ Xác thực cấu trúc Public Portal API thành công!")

        # 9. Dọn dẹp khôi phục trạng thái mặc định của vi ban đầu
        logger.info("🧹 9. Khôi phục lại ngôn ngữ mặc định (vi)")
        await ac.patch(f"/api/v1/languages/{vi_lang['id']}/set-default", headers=headers)
        logger.info("✅ Khôi phục thành công!")

if __name__ == "__main__":
    logger.info("🚀 Bắt đầu test API flow cho Module Language (Chế độ Đa ngôn ngữ Cố định)...")
    asyncio.run(test_api_flow())
    logger.info("🎉 Tất cả các bước test API flow đã thành công hoàn toàn!")
