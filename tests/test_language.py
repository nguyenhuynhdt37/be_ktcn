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
async def test_create_and_get_language(db_session):
    """Test tạo mới và lấy thông tin ngôn ngữ."""
    payload = LanguageCreate(
        code="tsone",
        name="Test Language 1",
        native_name="Ngôn ngữ test 1",
        flag_icon="/flags/tsone.svg",
        is_default=False,
        is_active=True,
        sort_order=5
    )
    lang = await language_service.create_language(db_session, payload)
    await db_session.commit()

    assert lang.id is not None
    assert lang.code == "tsone"
    assert lang.name == "Test Language 1"
    assert lang.flag_icon == "/flags/tsone.svg"
    assert lang.is_default is False

    # Thử lấy lại theo ID
    fetched = await language_service.get_language_by_id(db_session, lang.id)
    assert fetched.id == lang.id

    # Thử lấy theo Code
    fetched_by_code = await language_repository.get_by_code(db_session, "tsone")
    assert fetched_by_code is not None
    assert fetched_by_code.id == lang.id


@pytest.mark.asyncio
async def test_duplicate_code_raises_conflict(db_session):
    """Test tạo trùng code sẽ ném ngoại lệ ConflictException."""
    payload = LanguageCreate(
        code="tsdup",
        name="Test Dup",
        native_name="Dup",
        is_default=False
    )
    await language_service.create_language(db_session, payload)
    await db_session.commit()

    with pytest.raises(ConflictException):
        await language_service.create_language(db_session, payload)


@pytest.mark.asyncio
async def test_only_one_default_language(db_session):
    """Test quy tắc chỉ có duy nhất một default language (khi set default mới, default cũ tự tắt)."""
    # Lấy default hiện tại (thường là vi)
    old_default = await language_repository.get_default(db_session)
    assert old_default is not None
    assert old_default.is_default is True

    # Tạo ngôn ngữ test mới làm default
    payload = LanguageCreate(
        code="tsdef",
        name="Test Default",
        native_name="Default",
        is_default=True
    )
    new_default = await language_service.create_language(db_session, payload)
    await db_session.commit()

    assert new_default.is_default is True

    # Refresh old default từ DB để kiểm tra xem đã bị chuyển sang False chưa
    await db_session.refresh(old_default)
    assert old_default.is_default is False


@pytest.mark.asyncio
async def test_cannot_delete_default_language(db_session):
    """Test không cho phép xóa ngôn ngữ mặc định."""
    default_lang = await language_repository.get_default(db_session)
    assert default_lang is not None

    with pytest.raises(BadRequestException, match="Không thể xóa ngôn ngữ mặc định"):
        await language_service.delete_language(db_session, default_lang.id)


@pytest.mark.asyncio
async def test_cannot_delete_system_language(db_session):
    """Test không cho phép xóa ngôn ngữ hệ thống (is_system = True)."""
    # Lấy ngôn ngữ 'en' (là system language nhưng không phải default)
    en_lang = await language_repository.get_by_code(db_session, "en")
    assert en_lang is not None
    assert en_lang.is_system is True

    with pytest.raises(BadRequestException, match="Không thể xóa ngôn ngữ hệ thống"):
        await language_service.delete_language(db_session, en_lang.id)


@pytest.mark.asyncio
async def test_cannot_disable_default_language(db_session):
    """Test không cho phép disable ngôn ngữ mặc định."""
    default_lang = await language_repository.get_default(db_session)
    assert default_lang is not None

    with pytest.raises(BadRequestException, match="Không thể vô hiệu hóa ngôn ngữ mặc định"):
        await language_service.disable_language(db_session, default_lang.id)


@pytest.mark.asyncio
async def test_soft_delete_and_restore(db_session):
    """Test quy trình xóa mềm và khôi phục ngôn ngữ."""
    payload = LanguageCreate(
        code="tsdel",
        name="Test Delete",
        native_name="Delete",
        is_default=False
    )
    lang = await language_service.create_language(db_session, payload)
    await db_session.commit()

    # Xóa mềm
    await language_service.delete_language(db_session, lang.id)
    await db_session.commit()

    # Thử lấy lại bằng get_language_by_id -> sẽ báo NotFoundException
    with pytest.raises(NotFoundException):
        await language_service.get_language_by_id(db_session, lang.id)

    # Khôi phục
    restored = await language_service.restore_language(db_session, lang.id)
    await db_session.commit()

    assert restored.deleted_at is None
    
    # Lấy lại thành công
    fetched = await language_service.get_language_by_id(db_session, lang.id)
    assert fetched.id == lang.id


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
    assert "is_default" in first_item
    
    # Không được trả dữ liệu quản trị
    assert "is_active" not in first_item
    assert "sort_order" not in first_item
    assert "deleted_at" not in first_item
    assert "created_at" not in first_item


@pytest.mark.asyncio
async def test_admin_crud_flow_api(client: AsyncClient, admin_headers: dict):
    """Test toàn bộ luồng CRUD thông qua Admin API endpoints."""
    # 1. POST - Tạo mới ngôn ngữ
    post_payload = {
        "code": "tsapi",
        "name": "Test API Lang",
        "native_name": "API Lang Native",
        "is_default": False,
        "sort_order": 10,
        "is_active": True
    }
    create_res = await client.post("/api/v1/languages", json=post_payload, headers=admin_headers)
    assert create_res.status_code == 201
    lang_data = create_res.json()
    lang_id = lang_data["id"]
    assert lang_data["code"] == "tsapi"

    # 2. GET - Lấy danh sách ngôn ngữ
    list_res = await client.get("/api/v1/languages", headers=admin_headers)
    assert list_res.status_code == 200
    assert any(item["id"] == lang_id for item in list_res.json())

    # 3. GET - Chi tiết
    detail_res = await client.get(f"/api/v1/languages/{lang_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["name"] == "Test API Lang"

    # 4. PUT - Cập nhật
    update_payload = {
        "name": "Updated API Lang",
        "sort_order": 20
    }
    update_res = await client.put(f"/api/v1/languages/{lang_id}", json=update_payload, headers=admin_headers)
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated API Lang"
    assert update_res.json()["sort_order"] == 20

    # 5. PATCH - Disable
    disable_res = await client.patch(f"/api/v1/languages/{lang_id}/disable", headers=admin_headers)
    assert disable_res.status_code == 200
    assert disable_res.json()["is_active"] is False

    # 6. PATCH - Enable
    enable_res = await client.patch(f"/api/v1/languages/{lang_id}/enable", headers=admin_headers)
    assert enable_res.status_code == 200
    assert enable_res.json()["is_active"] is True

    # 7. PATCH - Set Default
    set_default_res = await client.patch(f"/api/v1/languages/{lang_id}/set-default", headers=admin_headers)
    assert set_default_res.status_code == 200
    assert set_default_res.json()["is_default"] is True

    # 8. DELETE - Xóa mềm
    # Trước tiên phải set default cho vi lại để được phép xóa tsapi
    # Lấy vi ID
    vi_lang_res = await client.get("/api/v1/languages", headers=admin_headers)
    vi_lang_id = next(item["id"] for item in vi_lang_res.json() if item["code"] == "vi")
    await client.patch(f"/api/v1/languages/{vi_lang_id}/set-default", headers=admin_headers)

    # Tiến hành xóa mềm tsapi
    delete_res = await client.delete(f"/api/v1/languages/{lang_id}", headers=admin_headers)
    assert delete_res.status_code == 204

    # 9. GET chi tiết -> 404
    get_deleted_res = await client.get(f"/api/v1/languages/{lang_id}", headers=admin_headers)
    assert get_deleted_res.status_code == 404

    # 10. PATCH - Restore
    restore_res = await client.patch(f"/api/v1/languages/{lang_id}/restore", headers=admin_headers)
    assert restore_res.status_code == 200
    assert restore_res.json()["deleted_at"] is None


# ──────────────────────────────────────────────────────────────────────────────
# VALIDATION TESTS
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("invalid_code", [
    "TS",        # Chứa chữ hoa
    "ts_1",      # Chứa dấu gạch dưới
    "ts-1",      # Chứa dấu gạch ngang
    "ts100000000", # Quá 10 ký tự (11 ký tự)
])
@pytest.mark.asyncio
async def test_invalid_code_validation_api(client: AsyncClient, admin_headers: dict, invalid_code: str):
    """Test validation không cho phép code sai định dạng."""
    payload = {
        "code": invalid_code,
        "name": "Invalid Lang",
        "native_name": "Invalid",
        "is_default": False
    }
    res = await client.post("/api/v1/languages", json=payload, headers=admin_headers)
    assert res.status_code == 422
    details = res.json()["error"]["details"]
    assert any("code" in k for k in details.keys())


@pytest.mark.asyncio
async def test_invalid_sort_order_validation_api(client: AsyncClient, admin_headers: dict):
    """Test validation không cho phép sort_order âm."""
    payload = {
        "code": "tsval",
        "name": "Invalid Order",
        "native_name": "Invalid",
        "is_default": False,
        "sort_order": -1
    }
    res = await client.post("/api/v1/languages", json=payload, headers=admin_headers)
    assert res.status_code == 422
    details = res.json()["error"]["details"]
    assert any("sort_order" in k for k in details.keys())


@pytest.mark.asyncio
async def test_admin_delete_system_language_api(client: AsyncClient, admin_headers: dict):
    """Test API ngăn chặn xóa ngôn ngữ hệ thống."""
    # Lấy ID của en
    list_res = await client.get("/api/v1/languages", headers=admin_headers)
    assert list_res.status_code == 200
    en_lang_id = next(item["id"] for item in list_res.json() if item["code"] == "en")
    
    # Gửi yêu cầu DELETE -> 400 Bad Request
    del_res = await client.delete(f"/api/v1/languages/{en_lang_id}", headers=admin_headers)
    assert del_res.status_code == 400
    assert del_res.json()["error"]["message"] == "Không thể xóa ngôn ngữ hệ thống"


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
