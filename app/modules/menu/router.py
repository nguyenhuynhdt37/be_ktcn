import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.audit.service import log_action
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.menu.schemas import (
    MenuCreate,
    MenuItemCreate,
    MenuItemReorderRequest,
    MenuItemResponse,
    MenuItemUpdate,
    MenuResponse,
    MenuTreeResponse,
    MenuUpdate,
    IconCategory,
)
from app.modules.menu.models import MenuItemTargetType
from app.modules.menu.service import menu_service
from app.modules.menu.target_resolver import target_resolver

menu_router = APIRouter()


# ──────────────────────────────────────────────
# Curated Icons Config
# ──────────────────────────────────────────────

@menu_router.get("/config/icons", response_model=list[IconCategory])
async def get_curated_icons(
    current_user: UserResponse = Depends(get_current_user),
) -> list[IconCategory]:
    """
    Lấy danh sách các Icon khuyên dùng dành cho website Trường đại học (dùng Lucide Icons/FontAwesome).
    Phục vụ cho việc chọn nhanh icon tại cấu hình Menu Item.
    Quyền yêu cầu: menu.view
    """
    return [
        IconCategory(
            category="Học thuật & Đào tạo",
            icons=[
                {"name": "Đào tạo / Sách", "code": "graduation-cap"},
                {"name": "Sách vở / Tài liệu", "code": "book-open"},
                {"name": "Kính hiển vi / Thí nghiệm", "code": "microscope"},
                {"name": "Lớp học / Bảng đen", "code": "presentation"},
                {"name": "Thư viện / Nghiên cứu", "code": "library"},
                {"name": "Bằng tốt nghiệp", "code": "award"},
            ]
        ),
        IconCategory(
            category="Tổ chức & Giới thiệu",
            icons=[
                {"name": "Giới thiệu / Thông tin", "code": "info"},
                {"name": "Tòa nhà / Trường học", "code": "school"},
                {"name": "Sơ đồ / Cơ cấu", "code": "git-branch"},
                {"name": "Đội ngũ / Con người", "code": "users"},
                {"name": "Lịch sử / Đồng hồ", "code": "history"},
                {"name": "Liên hệ / Hòm thư", "code": "mail"},
                {"name": "Bản đồ / Địa chỉ", "code": "map-pin"},
            ]
        ),
        IconCategory(
            category="Hoạt động & Tiện ích",
            icons=[
                {"name": "Tin tức / Báo chí", "code": "newspaper"},
                {"name": "Sự kiện / Lịch", "code": "calendar"},
                {"name": "Thông báo / Loa", "code": "megaphone"},
                {"name": "Biểu mẫu / Tệp tin", "code": "file-text"},
                {"name": "Tuyển dụng / Việc làm", "code": "briefcase"},
                {"name": "Hỏi đáp (FAQ)", "code": "help-circle"},
            ]
        ),
        IconCategory(
            category="Liên kết mạng xã hội",
            icons=[
                {"name": "Facebook", "code": "facebook"},
                {"name": "Youtube", "code": "youtube"},
                {"name": "Website ngoài", "code": "external-link"},
                {"name": "Trang chủ / Home", "code": "home"},
            ]
        )
    ]


# ──────────────────────────────────────────────
# Menu CRUD
# ──────────────────────────────────────────────


@menu_router.get("", response_model=list[MenuResponse])
async def list_menus(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MenuResponse]:
    """
    Lấy danh sách tất cả menus.
    Quyền yêu cầu: menu.view
    """
    menus = await menu_service.list_menus(db)
    return [MenuResponse.model_validate(m) for m in menus]


@menu_router.post("", response_model=MenuResponse, status_code=201)
async def create_menu(
    request: Request,
    payload: MenuCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MenuResponse:
    """
    Tạo menu mới.
    Quyền yêu cầu: menu.create
    """
    menu = await menu_service.create_menu(db, payload)
    await log_action(
        db, current_user, "MENU_CREATED", "menu", menu.id,
        {"name": payload.name, "code": payload.code},
        request,
    )
    await db.commit()
    return MenuResponse.model_validate(menu)


@menu_router.get("/code/{code}", response_model=MenuTreeResponse)
async def get_menu_tree_by_code(
    code: str,
    db: AsyncSession = Depends(get_db),
) -> MenuTreeResponse:
    """
    Lấy cây menu theo code (ví dụ: header, sidebar, footer) mà không cần xác thực token (Public API).
    """
    return await menu_service.get_menu_tree_by_code(db, code)



@menu_router.get("/{menu_id}", response_model=MenuResponse)
async def get_menu(
    menu_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MenuResponse:
    """
    Lấy chi tiết menu theo ID.
    Quyền yêu cầu: menu.view
    """
    menu = await menu_service.get_menu_by_id(db, menu_id)
    return MenuResponse.model_validate(menu)


@menu_router.put("/{menu_id}", response_model=MenuResponse)
async def update_menu(
    request: Request,
    menu_id: uuid.UUID,
    payload: MenuUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MenuResponse:
    """
    Cập nhật thông tin menu.
    Quyền yêu cầu: menu.update
    """
    menu = await menu_service.update_menu(db, menu_id, payload)
    await log_action(
        db, current_user, "MENU_UPDATED", "menu", menu.id,
        payload.model_dump(exclude_unset=True),
        request,
    )
    await db.commit()
    return MenuResponse.model_validate(menu)


@menu_router.delete("/{menu_id}", status_code=204)
async def delete_menu(
    request: Request,
    menu_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Xóa menu (cascade xóa tất cả menu items).
    Quyền yêu cầu: menu.delete
    """
    await menu_service.delete_menu(db, menu_id)
    await log_action(
        db, current_user, "MENU_DELETED", "menu", menu_id, None, request,
    )
    await db.commit()


# ──────────────────────────────────────────────
# Menu Tree (Admin kéo thả)
# ──────────────────────────────────────────────


@menu_router.get("/{menu_id}/tree", response_model=MenuTreeResponse)
async def get_menu_tree(
    menu_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MenuTreeResponse:
    """
    Lấy cây menu đầy đủ theo ID (cho admin kéo thả).
    Backend build tree sẵn trước khi trả về.
    Quyền yêu cầu: menu.view
    """
    return await menu_service.get_menu_tree_by_id(db, menu_id)


@menu_router.put("/{menu_id}/reorder")
async def reorder_menu_items(
    request: Request,
    menu_id: uuid.UUID,
    payload: MenuItemReorderRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Batch update sort_order và parent_id cho kéo thả menu.
    Frontend gửi toàn bộ items với vị trí mới sau khi kéo thả.
    Validate depth và circular reference cho toàn bộ batch.
    Quyền yêu cầu: menu.update
    """
    await menu_service.reorder_items(db, menu_id, payload)
    await log_action(
        db, current_user, "MENU_ITEMS_REORDERED", "menu", menu_id,
        {"items_count": len(payload.items)},
        request,
    )
    await db.commit()
    return {"success": True, "reordered": len(payload.items)}


# ──────────────────────────────────────────────
# Menu Item CRUD
# ──────────────────────────────────────────────


@menu_router.post(
    "/{menu_id}/items", response_model=MenuItemResponse, status_code=201
)
async def create_menu_item(
    request: Request,
    menu_id: uuid.UUID,
    payload: MenuItemCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MenuItemResponse:
    """
    Tạo menu item mới trong một menu.
    Quyền yêu cầu: menu.update
    """
    item = await menu_service.create_menu_item(db, menu_id, payload)
    await log_action(
        db, current_user, "MENU_ITEM_CREATED", "menu_item", item.id,
        {"title": payload.title, "menu_id": str(menu_id)},
        request,
    )
    await db.commit()
    # Resolve target_info cho response
    resolved_info = None
    if item.target_type and item.target_type != MenuItemTargetType.EXTERNAL_LINK and item.target_id:
        resolved_info = await target_resolver.resolve(db, item.target_type.value, item.target_id)
    return menu_service._to_item_response(item, target_info=resolved_info)


@menu_router.get("/{menu_id}/items/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(
    menu_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MenuItemResponse:
    """
    Lấy chi tiết menu item (cho panel config khi click vào item).
    Quyền yêu cầu: menu.view
    """
    return await menu_service.get_menu_item(db, menu_id, item_id)


@menu_router.put("/{menu_id}/items/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    request: Request,
    menu_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: MenuItemUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MenuItemResponse:
    """
    Cập nhật chi tiết menu item (title, target, icon...).
    Dùng cho panel config. Kéo thả dùng reorder API.
    Quyền yêu cầu: menu.update
    """
    item = await menu_service.update_menu_item(db, menu_id, item_id, payload)
    await log_action(
        db, current_user, "MENU_ITEM_UPDATED", "menu_item", item.id,
        payload.model_dump(exclude_unset=True, mode="json"),
        request,
    )
    await db.commit()
    # Resolve target_info cho response
    resolved_info = None
    if item.target_type and item.target_type != MenuItemTargetType.EXTERNAL_LINK and item.target_id:
        resolved_info = await target_resolver.resolve(db, item.target_type.value, item.target_id)
    return menu_service._to_item_response(item, target_info=resolved_info)


@menu_router.delete("/{menu_id}/items/{item_id}", status_code=204)
async def delete_menu_item(
    request: Request,
    menu_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Xóa menu item (cascade xóa children).
    Quyền yêu cầu: menu.update
    """
    await menu_service.delete_menu_item(db, menu_id, item_id)
    await log_action(
        db, current_user, "MENU_ITEM_DELETED", "menu_item", item_id,
        {"menu_id": str(menu_id)},
        request,
    )
    await db.commit()
