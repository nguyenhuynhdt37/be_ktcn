import asyncio
import sys
from loguru import logger
import httpx

from app.core.config import settings

# Cấu hình logger
logger.remove()
logger.add(sys.stderr, level="INFO")

async def test_translation_flow():
    # Sử dụng AsyncClient kết nối trực tiếp app qua ASGI để test nhanh
    from app.main import app
    from app.modules.translation import translation_service
    
    logger.info("⏳ Khởi động và warmup mô hình NLLB-200...")
    translation_service.warmup()
    
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

        logger.info("⚙️ Chuyển active model sang mock-model để test không bị rate limit/401")
        set_model_res = await ac.post(
            "/api/v1/translation/ai/settings",
            json={"active_model": "mock-model"},
            headers=headers
        )
        assert set_model_res.status_code == 200, f"Cập nhật model thất bại: {set_model_res.text}"

        # Từ khóa cần test
        test_phrase = "Thông báo tuyển sinh năm 2026"

        logger.info("🤖 2. Thực hiện dịch tự động đơn lẻ có Context (Tiếng Việt -> Anh)")
        logger.info(f"📤 Gửi yêu cầu dịch: '{test_phrase}'")
        res = await ac.post(
            "/api/v1/translation",
            json={"text": test_phrase, "target_languages": ["en"], "context": "article_title"},
            headers=headers,
            timeout=120.0
        )
        assert res.status_code == 200, f"Dịch thất bại: {res.text}"
        data = res.json()
        
        logger.info(f"✨ Kết quả dịch đơn lẻ:")
        logger.info(f"  [vi]: {data.get('vi')}")
        logger.info(f"  [en]: {data.get('en')}")
        logger.info("-" * 40)

        # Test dịch 1 ngôn ngữ đích (en)
        logger.info("🤖 3. Dịch đơn lẻ có Context khác (Tiếng Việt -> Anh)")
        res_single = await ac.post(
            "/api/v1/translation",
            json={"text": test_phrase, "target_languages": ["en"], "context": "short_description"},
            headers=headers,
        )
        assert res_single.status_code == 200
        data_single = res_single.json()
        assert "en" in data_single
        assert "lo" not in data_single
        logger.info("✅ Chỉ dịch sang tiếng Anh thành công!")
        logger.info("-" * 40)

        # Test dịch Batch
        batch_phrases = ["Thông báo", "Tuyển sinh", "Nghiên cứu khoa học"]
        logger.info("🤖 4. Thực hiện dịch tự động Batch có Context (Tiếng Việt -> Anh)")
        logger.info(f"📤 Gửi yêu cầu dịch batch cho {len(batch_phrases)} chuỗi")
        res_batch = await ac.post(
            "/api/v1/translation/batch",
            json={"texts": batch_phrases, "target_languages": ["en"], "context": "category_name"},
            headers=headers,
        )
        assert res_batch.status_code == 200, f"Dịch batch thất bại: {res_batch.text}"
        batch_data = res_batch.json()
        assert len(batch_data) == 3
        
        logger.info(f"✨ Kết quả dịch batch:")
        for idx, item in enumerate(batch_data):
            logger.info(f"  Item {idx}:")
            logger.info(f"    [vi]: {item.get('vi')}")
            logger.info(f"    [en]: {item.get('en')}")
        logger.info("-" * 40)

        # Test Validation: Text rỗng
        logger.info("⚠️ 5. Kiểm tra validation: Gửi text rỗng")
        res_val = await ac.post(
            "/api/v1/translation",
            json={"text": "", "target_languages": ["en"]},
            headers=headers,
        )
        assert res_val.status_code == 400
        assert res_val.json()["error"]["code"] == "TRANSLATION_INVALID_INPUT"
        logger.info("✅ Chặn text rỗng thành công!")

        # Test Validation: Ngôn ngữ đích không hợp lệ
        logger.info("⚠️ 6. Kiểm tra validation: Gửi ngôn ngữ không hỗ trợ")
        res_lang_val = await ac.post(
            "/api/v1/translation",
            json={"text": "Hello", "target_languages": ["fr"]},
            headers=headers,
        )
        assert res_lang_val.status_code == 422
        logger.info("✅ Chặn ngôn ngữ đích không hợp lệ thành công!")

        # Test Validation: Context không hợp lệ
        logger.info("⚠️ 7. Kiểm tra validation: Gửi context không tồn tại")
        res_context_val = await ac.post(
            "/api/v1/translation",
            json={"text": "Hello", "target_languages": ["en"], "context": "invalid_context_code"},
            headers=headers,
        )
        assert res_context_val.status_code == 422
        logger.info("✅ Chặn context không hợp lệ thành công!")

        logger.info("⚙️ Khôi phục active model về gemini-2.5-flash...")
        restore_model_res = await ac.post(
            "/api/v1/translation/ai/settings",
            json={"active_model": "gemini-2.5-flash"},
            headers=headers
        )
        assert restore_model_res.status_code == 200, f"Khôi phục model thất bại: {restore_model_res.text}"

        logger.info("🎉 Tất cả các bước test API dịch thuật tự động đã thành công hoàn toàn!")

if __name__ == "__main__":
    logger.info("🚀 Bắt đầu test API dịch tự động NLLB-200 chuẩn Production...")
    asyncio.run(test_translation_flow())
