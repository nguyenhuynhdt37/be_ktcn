import uuid
from typing import Optional

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
    AdminMenuItemResponse,
    MenuItemUpdate,
    AdminMenuResponse,
    AdminMenuTreeResponse,
    MenuUpdate,
)
from app.modules.menu.service import menu_service
from app.modules.menu.target_resolver import target_resolver

admin_router = APIRouter()


@admin_router.get("", response_model=list[AdminMenuResponse])
async def list_menus_admin(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AdminMenuResponse]:
    """
    [CMS Admin] Lấy danh sách tất cả các menu.
    """
    menus = await menu_service.list_menus(db)
    return [AdminMenuResponse.model_validate(m) for m in menus]


@admin_router.get("/{menu_id}", response_model=AdminMenuResponse)
async def get_menu_admin(
    menu_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminMenuResponse:
    """
    [CMS Admin] Lấy thông tin chi tiết một menu theo ID.
    """
    menu = await menu_service.get_menu_by_id(db, menu_id)
    return AdminMenuResponse.model_validate(menu)


@admin_router.post("", response_model=AdminMenuResponse, status_code=201)
async def create_menu_admin(
    request: Request,
    payload: MenuCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminMenuResponse:
    """
    [CMS Admin] Tạo mới một menu.
    """
    menu = await menu_service.create_menu(db, payload)
    await log_action(
        db, current_user, "MENU_CREATED", "menu", menu.id,
        {"code": menu.code, "name": menu.name},
        request
    )
    await db.commit()
    return AdminMenuResponse.model_validate(menu)


@admin_router.put("/{menu_id}", response_model=AdminMenuResponse)
async def update_menu_admin(
    request: Request,
    menu_id: uuid.UUID,
    payload: MenuUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminMenuResponse:
    """
    [CMS Admin] Cập nhật thông tin menu.
    """
    menu = await menu_service.update_menu(db, menu_id, payload)
    await log_action(
        db, current_user, "MENU_UPDATED", "menu", menu.id,
        payload.model_dump(exclude_unset=True),
        request
    )
    await db.commit()
    return AdminMenuResponse.model_validate(menu)


@admin_router.delete("/{menu_id}", status_code=204)
async def delete_menu_admin(
    request: Request,
    menu_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    [CMS Admin] Xóa menu.
    """
    await menu_service.delete_menu(db, menu_id)
    await log_action(db, current_user, "MENU_DELETED", "menu", menu_id, None, request)
    await db.commit()


@admin_router.get("/{menu_id}/tree", response_model=AdminMenuTreeResponse)
async def get_menu_tree_admin(
    menu_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminMenuTreeResponse:
    """
    [CMS Admin] Lấy cây menu đệ quy đầy đủ để Admin kéo thả cấu trúc.
    """
    tree = await menu_service.get_menu_tree_by_id(db, menu_id, lang="vi")
    return AdminMenuTreeResponse.model_validate(tree)


@admin_router.post("/{menu_id}/items", response_model=AdminMenuItemResponse, status_code=201)
async def create_menu_item_admin(
    request: Request,
    menu_id: uuid.UUID,
    payload: MenuItemCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminMenuItemResponse:
    """
    [CMS Admin] Thêm mục menu (MenuItem) mới.
    """
    item = await menu_service.create_menu_item(db, menu_id, payload, lang="vi")
    await log_action(
        db, current_user, "MENU_ITEM_CREATED", "menu_item", item.id,
        {"menu_id": str(menu_id), "title": getattr(item, "title", "")},
        request
    )
    await db.commit()
    return AdminMenuItemResponse.model_validate(item)

@admin_router.put("/{menu_id}/items/reorder", status_code=200)
async def reorder_menu_items_admin(
    request: Request,
    menu_id: uuid.UUID,
    payload: MenuItemReorderRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    [CMS Admin] Cập nhật đồng loạt vị trí kéo thả các mục menu.
    """
    await menu_service.reorder_items(db, menu_id, payload)
    await log_action(
        db, current_user, "MENU_ITEMS_REORDERED", "menu", menu_id,
        {"items_count": len(payload.items)},
        request
    )
    await db.commit()
    return {"success": True, "reordered": len(payload.items)}



@admin_router.get("/{menu_id}/items/{item_id}", response_model=AdminMenuItemResponse)
async def get_menu_item_admin(
    menu_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminMenuItemResponse:
    """
    [CMS Admin] Lấy chi tiết cấu hình một mục menu.
    """
    item = await menu_service.get_menu_item(db, menu_id, item_id, lang="vi")
    return AdminMenuItemResponse.model_validate(item)


@admin_router.put("/{menu_id}/items/{item_id}", response_model=AdminMenuItemResponse)
async def update_menu_item_admin(
    request: Request,
    menu_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: MenuItemUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminMenuItemResponse:
    """
    [CMS Admin] Cập nhật chi tiết một mục menu.
    """
    item = await menu_service.update_menu_item(db, menu_id, item_id, payload, lang="vi")
    await log_action(
        db, current_user, "MENU_ITEM_UPDATED", "menu_item", item.id,
        payload.model_dump(exclude_unset=True),
        request
    )
    await db.commit()
    return AdminMenuItemResponse.model_validate(item)


@admin_router.delete("/{menu_id}/items/{item_id}", status_code=204)
async def delete_menu_item_admin(
    request: Request,
    menu_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    [CMS Admin] Xóa mục menu.
    """
    await menu_service.delete_menu_item(db, menu_id, item_id)
    await log_action(
        db, current_user, "MENU_ITEM_DELETED", "menu_item", item_id,
        {"menu_id": str(menu_id)},
        request
    )
    await db.commit()



