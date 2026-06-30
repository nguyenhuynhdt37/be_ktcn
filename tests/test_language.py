import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select, delete

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.modules.language.models import Language
from app.modules.language.repository import language_repository
from app.modules.language.service import language_service
from app.modules.language.schemas import LanguageCreate, LanguageUpdate


@pytest.fixture(autouse=True)
async def cleanup_test_languages(db_session):
    """
    Tự động dọn dẹp các ngôn ngữ test sau mỗi test case.
    Các ngôn ngữ test sẽ có code bắt đầu bằng 'ts'.
    """
    yield
    # Teardown: xóa tất cả ngôn ngữ bắt đầu bằng 'ts' để không làm bẩn DB thực
    await db_session.execute(
        delete(Language).where(Language.code.like("ts%"))
    )
    # Khôi phục trạng thái ban đầu của vi làm default nếu có test case nào thay đổi default
    # Thường thì vi, en, lo đã được seed sẵn và vi là default.
    # Đảm bảo vi vẫn là default
    vi_lang_res = await db_session.execute(
        select(Language).where(Language.code == "vi")
    )
    vi_lang = vi_lang_res.scalar_one_or_none()
    if vi_lang and not vi_lang.is_default:
        await language_repository.set_default(db_session, vi_lang.id)
    await db_session.commit()


# ──────────────────────────────────────────────────────────────────────────────
# SERVICE & REPOSITORY TESTS
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_only_one_default_language(db_session):
    """Test quy tắc chỉ có duy nhất một default language (khi set default mới, default cũ tự tắt)."""
    # Lấy default hiện tại (thường là vi)
    old_default = await language_repository.get_default(db_session)
    assert old_default is not None
    assert old_default.is_default is True

    # Lấy ngôn ngữ 'en' để set default
    en_lang = await language_repository.get_by_code(db_session, "en")
    assert en_lang is not None
    assert en_lang.is_default is False

    # Set default cho en
    await language_service.set_default_language(db_session, en_lang.id)
    await db_session.commit()

    # Refresh để kiểm tra
    await db_session.refresh(old_default)
    await db_session.refresh(en_lang)
    
    assert en_lang.is_default is True
    assert old_default.is_default is False

    # Reset lại vi làm mặc định để không ảnh hưởng test case khác
    await language_service.set_default_language(db_session, old_default.id)
    await db_session.commit()


@pytest.mark.asyncio
async def test_cannot_disable_default_language(db_session):
    """Test không cho phép disable ngôn ngữ mặc định."""
    default_lang = await language_repository.get_default(db_session)
    assert default_lang is not None

    with pytest.raises(BadRequestException, match="Không thể vô hiệu hóa ngôn ngữ mặc định"):
        await language_service.disable_language(db_session, default_lang.id)


# ──────────────────────────────────────────────────────────────────────────────
# API ENDPOINT TESTS
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_portal_languages_api(client: AsyncClient):
    """Test Public Portal API trả về đúng schema rút gọn."""
    res = await client.get("/api/v1/portal/languages")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    
    # Verify cấu trúc schema PortalLanguageResponse
    first_item = data[0]
    assert "id" in first_item
    assert "code" in first_item
    assert "name" in first_item
    assert "native_name" in first_item
    assert "flag_id" in first_item
    assert "flag_url" in first_item
    assert "is_default" in first_item
    
    # Không được trả dữ liệu quản trị
    assert "is_active" not in first_item
    assert "sort_order" not in first_item
    assert "deleted_at" not in first_item
    assert "created_at" not in first_item


@pytest.mark.asyncio
async def test_admin_language_api_flow(client: AsyncClient, admin_headers: dict):
    """Test luồng API Admin khả dụng (List, Get, Enable, Disable, Set Default)."""
    # 1. GET - Lấy danh sách ngôn ngữ
    list_res = await client.get("/api/v1/languages", headers=admin_headers)
    assert list_res.status_code == 200
    languages = list_res.json()
    assert len(languages) == 3  # Luôn có 3 ngôn ngữ hệ thống vi, en, lo
    
    vi_lang = next(item for item in languages if item["code"] == "vi")
    en_lang = next(item for item in languages if item["code"] == "en")
    
    # 2. GET - Chi tiết
    detail_res = await client.get(f"/api/v1/languages/{en_lang['id']}", headers=admin_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["code"] == "en"

    # 3. PATCH - Disable en
    disable_res = await client.patch(f"/api/v1/languages/{en_lang['id']}/disable", headers=admin_headers)
    assert disable_res.status_code == 200
    assert disable_res.json()["is_active"] is False

    # 4. PATCH - Enable en
    enable_res = await client.patch(f"/api/v1/languages/{en_lang['id']}/enable", headers=admin_headers)
    assert enable_res.status_code == 200
    assert enable_res.json()["is_active"] is True

    # 5. PATCH - Set Default en
    set_default_res = await client.patch(f"/api/v1/languages/{en_lang['id']}/set-default", headers=admin_headers)
    assert set_default_res.status_code == 200
    assert set_default_res.json()["is_default"] is True

    # Trả lại default cho vi
    await client.patch(f"/api/v1/languages/{vi_lang['id']}/set-default", headers=admin_headers)


@pytest.mark.asyncio
async def test_reorder_languages_api(client: AsyncClient, admin_headers: dict):
    """Test API cập nhật lại sort_order của các ngôn ngữ (kéo thả)."""
    # 1. Lấy danh sách ngôn ngữ hiện tại để có ID
    list_res = await client.get("/api/v1/languages", headers=admin_headers)
    assert list_res.status_code == 200
    languages = list_res.json()
    assert len(languages) >= 2
    
    # 2. Chuẩn bị payload thay đổi sort_order
    lang1 = languages[0]
    lang2 = languages[1]
    
    reorder_payload = {
        "items": [
            {"id": lang1["id"], "sort_order": 100},
            {"id": lang2["id"], "sort_order": 200}
        ]
    }
    
    # 3. Call API reorder
    reorder_res = await client.put("/api/v1/languages/reorder", json=reorder_payload, headers=admin_headers)
    assert reorder_res.status_code == 200
    assert reorder_res.json()["success"] is True
    assert reorder_res.json()["reordered"] == 2
    
    # 4. Lấy lại danh sách kiểm tra xem sort_order đã được cập nhật chưa
    new_list_res = await client.get("/api/v1/languages", headers=admin_headers)
    new_languages = {item["id"]: item for item in new_list_res.json()}
    
    assert new_languages[lang1["id"]]["sort_order"] == 100
    assert new_languages[lang2["id"]]["sort_order"] == 200
