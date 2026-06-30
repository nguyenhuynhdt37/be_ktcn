import asyncio
import uuid
import sys
import os
from loguru import logger
import httpx
from sqlalchemy import select, delete

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import SessionLocal
from app.modules.auth.models import User
from app.modules.language.models import Language
from app.core.security import hash_password


async def setup_test_user():
    async with SessionLocal() as db:
        existing = await db.execute(select(User).where(User.username == "admin_api_test"))
        user = existing.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.uuid4(), 
                username="admin_api_test", 
                email="admin_api@test.com", 
                password_hash=hash_password("password"), 
                full_name="Admin API Test", 
                is_active=True
            )
            db.add(user)
            await db.commit()
                    
        return "admin_api_test", "password"


async def cleanup_db():
    async with SessionLocal() as db:
        logger.info("🧹 Dọn dẹp dữ liệu test trong cơ sở dữ liệu...")
        await db.execute(delete(Language).where(Language.code == "tapi"))
        
        # Đảm bảo vi vẫn là default
        vi_res = await db.execute(select(Language).where(Language.code == "vi"))
        vi_lang = vi_res.scalar_one_or_none()
        if vi_lang and not vi_lang.is_default:
            # Tắt default của tất cả các bản ghi khác
            from sqlalchemy import update
            await db.execute(update(Language).values(is_default=False))
            vi_lang.is_default = True
            vi_lang.is_active = True
            db.add(vi_lang)
            
        await db.commit()
        logger.info("✅ Dọn dẹp hoàn tất!")


async def test_api_flow():
    username, password = await setup_test_user()
    
    # Dọn dẹp trước khi chạy để tránh lỗi trùng lặp
    await cleanup_db()
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        logger.info("🔑 1. Đăng nhập để lấy Token")
        login_res = await ac.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert login_res.status_code == 200, f"Đăng nhập thất bại: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("✅ Đăng nhập thành công!")

        logger.info("🌐 2. Tạo mới Ngôn ngữ")
        lang_data = {
            "code": "tapi",
            "name": "Test API Language",
            "native_name": "API Native",
            "flag_icon": "/flags/tapi.svg",
            "is_default": False,
            "is_active": True,
            "sort_order": 10
        }
        create_res = await ac.post("/api/v1/languages", json=lang_data, headers=headers)
        assert create_res.status_code == 201, f"Tạo ngôn ngữ thất bại: {create_res.text}"
        lang_json = create_res.json()
        lang_id = lang_json["id"]
        assert lang_json["is_system"] is False
        assert lang_json["flag_icon"] == "/flags/tapi.svg"
        logger.info(f"✅ Tạo thành công: ID={lang_id}, Code={lang_json['code']}")

        logger.info("🔍 3. Lấy chi tiết Ngôn ngữ vừa tạo")
        get_res = await ac.get(f"/api/v1/languages/{lang_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["name"] == lang_data["name"]
        logger.info("✅ Lấy chi tiết thành công!")

        logger.info("📋 4. Lấy danh sách Ngôn ngữ (Admin)")
        list_res = await ac.get("/api/v1/languages", headers=headers)
        assert list_res.status_code == 200
        logger.info(f"✅ Lấy danh sách thành công, tổng số ngôn ngữ: {len(list_res.json())}")

        logger.info("📝 5. Cập nhật Ngôn ngữ")
        update_data = {
            "name": "Test API Language Updated",
            "sort_order": 50
        }
        update_res = await ac.put(f"/api/v1/languages/{lang_id}", json=update_data, headers=headers)
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "Test API Language Updated"
        assert update_res.json()["sort_order"] == 50
        logger.info("✅ Cập nhật ngôn ngữ thành công!")

        logger.info("📐 5.5. Reorder Ngôn ngữ (Kéo thả)")
        vi_lang_id = next(item["id"] for item in list_res.json() if item["code"] == "vi")
        reorder_payload = {
            "items": [
                {"id": vi_lang_id, "sort_order": 100},
                {"id": lang_id, "sort_order": 200}
            ]
        }
        reorder_res = await ac.put("/api/v1/languages/reorder", json=reorder_payload, headers=headers)
        assert reorder_res.status_code == 200
        assert reorder_res.json()["success"] is True
        logger.info("✅ Reorder ngôn ngữ thành công!")

        logger.info("🔄 6. Cập nhật Trạng thái hoạt động (Disable/Enable)")
        # Disable
        disable_res = await ac.patch(f"/api/v1/languages/{lang_id}/disable", headers=headers)
        assert disable_res.status_code == 200
        assert disable_res.json()["is_active"] is False
        logger.info("✅ Vô hiệu hóa ngôn ngữ thành công!")

        # Enable
        enable_res = await ac.patch(f"/api/v1/languages/{lang_id}/enable", headers=headers)
        assert enable_res.status_code == 200
        assert enable_res.json()["is_active"] is True
        logger.info("✅ Kích hoạt lại ngôn ngữ thành công!")

        logger.info("👑 7. Thiết lập làm ngôn ngữ mặc định")
        default_res = await ac.patch(f"/api/v1/languages/{lang_id}/set-default", headers=headers)
        assert default_res.status_code == 200
        assert default_res.json()["is_default"] is True
        logger.info("✅ Thiết lập làm mặc định thành công!")

        logger.info("⚠️ 8. Kiểm tra validation: Không được xóa ngôn ngữ mặc định")
        del_fail_res = await ac.delete(f"/api/v1/languages/{lang_id}", headers=headers)
        assert del_fail_res.status_code == 400
        logger.info("✅ Ngăn chặn xóa mặc định chính xác!")

        logger.info("⚠️ 9. Kiểm tra validation: Không được disable ngôn ngữ mặc định")
        dis_fail_res = await ac.patch(f"/api/v1/languages/{lang_id}/disable", headers=headers)
        assert dis_fail_res.status_code == 400
        logger.info("✅ Ngăn chặn disable mặc định chính xác!")

        # Trả default về cho vi để được phép xóa tapi
        vi_lang_res = await ac.get("/api/v1/languages", headers=headers)
        vi_lang_id = next(item["id"] for item in vi_lang_res.json() if item["code"] == "vi")
        await ac.patch(f"/api/v1/languages/{vi_lang_id}/set-default", headers=headers)

        logger.info("⚠️ 9.5. Kiểm tra validation: Không được xóa ngôn ngữ hệ thống")
        en_lang_id = next(item["id"] for item in vi_lang_res.json() if item["code"] == "en")
        del_sys_fail_res = await ac.delete(f"/api/v1/languages/{en_lang_id}", headers=headers)
        assert del_sys_fail_res.status_code == 400
        assert del_sys_fail_res.json()["error"]["message"] == "Không thể xóa ngôn ngữ hệ thống"
        logger.info("✅ Ngăn chặn xóa ngôn ngữ hệ thống chính xác!")

        logger.info("🗑️ 10. Xóa Ngôn ngữ (Xóa mềm)")
        delete_res = await ac.delete(f"/api/v1/languages/{lang_id}", headers=headers)
        assert delete_res.status_code == 204
        logger.info("✅ Xóa mềm thành công!")

        logger.info("🎯 11. Xác nhận ngôn ngữ đã bị xóa mềm (Không tìm thấy)")
        get_deleted_res = await ac.get(f"/api/v1/languages/{lang_id}", headers=headers)
        assert get_deleted_res.status_code == 404
        logger.info("✅ Xác thực xóa mềm thành công!")

        logger.info("🔄 12. Khôi phục ngôn ngữ đã xóa mềm")
        restore_res = await ac.patch(f"/api/v1/languages/{lang_id}/restore", headers=headers)
        assert restore_res.status_code == 200
        assert restore_res.json()["deleted_at"] is None
        logger.info("✅ Khôi phục thành công!")

        logger.info("🌐 13. Lấy danh sách Public Portal API (Xác thực schema rút gọn)")
        portal_res = await ac.get("/api/v1/portal/languages")
        assert portal_res.status_code == 200
        portal_list = portal_res.json()
        assert len(portal_list) >= 1
        # Lấy bản ghi tapi trong list portal
        tapi_portal = next(item for item in portal_list if item["code"] == "tapi")
        assert "is_active" not in tapi_portal
        assert "sort_order" not in tapi_portal
        assert "deleted_at" not in tapi_portal
        logger.info("✅ Xác thực cấu trúc Public Portal API thành công!")

    # Dọn dẹp DB sau khi chạy xong
    await cleanup_db()


if __name__ == "__main__":
    logger.info("🚀 Bắt đầu test API flow cho Module Language...")
    asyncio.run(test_api_flow())
    logger.info("🎉 Tất cả các bước test API flow đã thành công hoàn toàn!")
