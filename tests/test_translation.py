import pytest
from httpx import AsyncClient
from unittest.mock import patch

from app.core.config import settings
from app.modules.translation.service import translation_service
from app.modules.translation.exceptions import InvalidInputException, BatchSizeExceededException

@pytest.mark.asyncio
async def test_translation_service_warmup():
    """Test warmup khởi động model dịch thuật."""
    # Đảm bảo model đã load thành công
    translation_service.warmup()
    assert translation_service._is_ready is True
    assert translation_service._model is not None
    assert translation_service._tokenizer is not None

@pytest.mark.asyncio
async def test_translation_validation():
    """Test validation đầu vào dịch thuật."""
    # Test rỗng
    with pytest.raises(InvalidInputException, match="Văn bản cần dịch không được để trống"):
        await translation_service.translate_text("", ["en"])

    # Test quá dài
    long_text = "A" * (settings.TRANSLATION_MAX_INPUT_LENGTH + 1)
    with pytest.raises(InvalidInputException, match="vượt quá giới hạn cho phép"):
        await translation_service.translate_text(long_text, ["en"])

    # Test ký tự ẩn/không hợp lệ
    invalid_text = "Hello \x00 World"
    with pytest.raises(InvalidInputException, match="chứa ký tự không hợp lệ"):
        await translation_service.translate_text(invalid_text, ["en"])

@pytest.mark.asyncio
async def test_single_translation_api(client: AsyncClient, admin_headers: dict):
    """Test API dịch đơn lẻ tiếng Việt -> Anh."""
    payload = {
        "text": "Khoa Khoa học Máy tính",
        "target_languages": ["en"]
    }
    res = await client.post("/api/v1/translation", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["vi"] == "Khoa Khoa học Máy tính"
    assert "en" in data
    assert len(data["en"]) > 0

@pytest.mark.asyncio
async def test_single_translation_api_single_target(client: AsyncClient, admin_headers: dict):
    """Test API dịch đơn lẻ chỉ dịch sang 1 ngôn ngữ chỉ định (en)."""
    payload = {
        "text": "Tuyển sinh năm 2026",
        "target_languages": ["en"]
    }
    res = await client.post("/api/v1/translation", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["vi"] == "Tuyển sinh năm 2026"
    assert "en" in data
    assert "lo" not in data  # Không chạy bản dịch tiếng Lào

@pytest.mark.asyncio
async def test_batch_translation_api(client: AsyncClient, admin_headers: dict):
    """Test API dịch hàng loạt (Batch translation)."""
    payload = {
        "texts": ["Tuyển sinh", "Nghiên cứu khoa học"],
        "target_languages": ["en"]
    }
    res = await client.post("/api/v1/translation/batch", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["vi"] == "Tuyển sinh"
    assert "en" in data[0]
    assert data[1]["vi"] == "Nghiên cứu khoa học"

@pytest.mark.asyncio
async def test_batch_size_exceeded_api(client: AsyncClient, admin_headers: dict):
    """Test validation batch size vượt quá giới hạn cấu hình."""
    payload = {
        "texts": ["Text"] * (settings.TRANSLATION_MAX_BATCH_SIZE + 1),
        "target_languages": ["en"]
    }
    res = await client.post("/api/v1/translation/batch", json=payload, headers=admin_headers)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "TRANSLATION_BATCH_SIZE_EXCEEDED"
