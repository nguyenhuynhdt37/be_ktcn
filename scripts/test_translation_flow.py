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

        # Từ khóa cần test
        test_phrase = "Thông báo tuyển sinh năm 2026"

        logger.info("🤖 2. Thực hiện dịch tự động NLLB-200 đơn lẻ (Tiếng Việt -> Anh & Lào)")
        logger.info(f"📤 Gửi yêu cầu dịch: '{test_phrase}'")
        res = await ac.post(
            "/api/v1/translation",
            json={"text": test_phrase, "target_languages": ["en", "lo"]},
            headers=headers,
            timeout=120.0  # Tăng timeout phòng trường hợp model download lần đầu tiên
        )
        assert res.status_code == 200, f"Dịch thất bại: {res.text}"
        data = res.json()
        
        logger.info(f"✨ Kết quả dịch đơn lẻ:")
        logger.info(f"  [vi]: {data.get('vi')}")
        logger.info(f"  [en]: {data.get('en')}")
        logger.info(f"  [lo]: {data.get('lo')}")
        logger.info("-" * 40)

        # Test dịch 1 ngôn ngữ đích (en)
        logger.info("🤖 3. Dịch đơn lẻ chỉ dịch sang 1 ngôn ngữ (Tiếng Việt -> Anh)")
        res_single = await ac.post(
            "/api/v1/translation",
            json={"text": test_phrase, "target_languages": ["en"]},
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
        logger.info("🤖 4. Thực hiện dịch tự động NLLB-200 Batch (Tiếng Việt -> Anh & Lào)")
        logger.info(f"📤 Gửi yêu cầu dịch batch cho {len(batch_phrases)} chuỗi")
        res_batch = await ac.post(
            "/api/v1/translation/batch",
            json={"texts": batch_phrases, "target_languages": ["en", "lo"]},
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
            logger.info(f"    [lo]: {item.get('lo')}")
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

        logger.info("🎉 Tất cả các bước test API dịch thuật tự động đã thành công hoàn toàn!")

if __name__ == "__main__":
    logger.info("🚀 Bắt đầu test API dịch tự động NLLB-200 chuẩn Production...")
    asyncio.run(test_translation_flow())
