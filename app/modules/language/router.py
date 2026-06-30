import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.audit.service import log_action
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.language.schemas import (
    LanguageCreate,
    LanguageResponse,
    LanguageUpdate,
    PortalLanguageResponse,
    LanguageReorderRequest,
)
from app.modules.language.service import language_service

admin_router = APIRouter()
portal_router = APIRouter()


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC PORTAL API
# ──────────────────────────────────────────────────────────────────────────────

@portal_router.get("", response_model=list[PortalLanguageResponse])
async def list_portal_languages(
    db: AsyncSession = Depends(get_db),
) -> list[PortalLanguageResponse]:
    """
    Lấy danh sách các ngôn ngữ đang hoạt động của hệ thống (Public API).
    Chỉ trả về các thông tin cơ bản: id, code, name, native_name, is_default.
    """
    languages = await language_service.list_portal_languages(db)
    return [PortalLanguageResponse.model_validate(lang) for lang in languages]


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN APIs (Yêu cầu Token quản trị)
# ──────────────────────────────────────────────────────────────────────────────

@admin_router.get("", response_model=list[LanguageResponse])
async def list_languages(
    show_deleted: bool = False,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LanguageResponse]:
    """
    Lấy danh sách tất cả các ngôn ngữ, bao gồm cả ngôn ngữ đang hoạt động và tạm khóa (Admin).
    """
    languages = await language_service.list_languages(db, show_deleted=show_deleted)
    return [LanguageResponse.model_validate(lang) for lang in languages]


@admin_router.put("/reorder", status_code=status.HTTP_200_OK)
async def reorder_languages(
    request: Request,
    payload: LanguageReorderRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Cập nhật đồng loạt vị trí kéo thả ngôn ngữ (sort_order).
    """
    await language_service.reorder_languages(db, payload)
    
    # Ghi nhận Audit Log
    await log_action(
        db,
        current_user,
        "LANGUAGES_REORDERED",
        "language",
        None,
        {"items_count": len(payload.items)},
        request,
    )
    await db.commit()
    return {"success": True, "reordered": len(payload.items)}


@admin_router.get("/{id}", response_model=LanguageResponse)
async def get_language(
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LanguageResponse:
    """
    Lấy chi tiết một ngôn ngữ theo ID (Admin).
    """
    lang = await language_service.get_language_by_id(db, id)
    return LanguageResponse.model_validate(lang)


@admin_router.post("", response_model=LanguageResponse, status_code=status.HTTP_201_CREATED)
async def create_language(
    request: Request,
    payload: LanguageCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LanguageResponse:
    """
    Tạo mới một ngôn ngữ trong hệ thống (Admin).
    """
    lang = await language_service.create_language(db, payload)
    
    # Ghi nhận Audit Log
    await log_action(
        db,
        current_user,
        "LANGUAGE_CREATED",
        "language",
        lang.id,
        {"code": lang.code, "name": lang.name, "is_default": lang.is_default},
        request,
    )
    await db.commit()
    return LanguageResponse.model_validate(lang)


@admin_router.put("/{id}", response_model=LanguageResponse)
async def update_language(
    request: Request,
    id: uuid.UUID,
    payload: LanguageUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LanguageResponse:
    """
    Cập nhật thông tin ngôn ngữ (Admin).
    """
    lang = await language_service.update_language(db, id, payload)
    
    # Ghi nhận Audit Log
    await log_action(
        db,
        current_user,
        "LANGUAGE_UPDATED",
        "language",
        lang.id,
        {"code": lang.code, "name": lang.name, "is_default": lang.is_default, "is_active": lang.is_active},
        request,
    )
    await db.commit()
    return LanguageResponse.model_validate(lang)


@admin_router.patch("/{id}/enable", response_model=LanguageResponse)
async def enable_language(
    request: Request,
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LanguageResponse:
    """
    Kích hoạt hoạt động cho ngôn ngữ (Admin).
    """
    lang = await language_service.enable_language(db, id)
    
    # Ghi nhận Audit Log
    await log_action(
        db,
        current_user,
        "LANGUAGE_ENABLED",
        "language",
        lang.id,
        {"code": lang.code, "is_active": True},
        request,
    )
    await db.commit()
    return LanguageResponse.model_validate(lang)


@admin_router.patch("/{id}/disable", response_model=LanguageResponse)
async def disable_language(
    request: Request,
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LanguageResponse:
    """
    Ngưng hoạt động của ngôn ngữ. Không thể vô hiệu hóa ngôn ngữ mặc định (Admin).
    """
    lang = await language_service.disable_language(db, id)
    
    # Ghi nhận Audit Log
    await log_action(
        db,
        current_user,
        "LANGUAGE_DISABLED",
        "language",
        lang.id,
        {"code": lang.code, "is_active": False},
        request,
    )
    await db.commit()
    return LanguageResponse.model_validate(lang)


@admin_router.patch("/{id}/set-default", response_model=LanguageResponse)
async def set_default_language(
    request: Request,
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LanguageResponse:
    """
    Thiết lập ngôn ngữ chỉ định làm ngôn ngữ mặc định của toàn hệ thống (Admin).
    """
    lang = await language_service.set_default_language(db, id)
    
    # Ghi nhận Audit Log
    await log_action(
        db,
        current_user,
        "LANGUAGE_SET_DEFAULT",
        "language",
        lang.id,
        {"code": lang.code, "is_default": True},
        request,
    )
    await db.commit()
    return LanguageResponse.model_validate(lang)


@admin_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_language(
    request: Request,
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Xóa mềm một ngôn ngữ. Không thể xóa ngôn ngữ mặc định (Admin).
    """
    lang = await language_service.delete_language(db, id)
    
    # Ghi nhận Audit Log
    await log_action(
        db,
        current_user,
        "LANGUAGE_DELETED",
        "language",
        id,
        {"code": lang.code, "name": lang.name},
        request,
    )
    await db.commit()


@admin_router.patch("/{id}/restore", response_model=LanguageResponse)
async def restore_language(
    request: Request,
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LanguageResponse:
    """
    Khôi phục một ngôn ngữ đã bị xóa mềm trước đó (Admin).
    """
    lang = await language_service.restore_language(db, id)
    
    # Ghi nhận Audit Log
    await log_action(
        db,
        current_user,
        "LANGUAGE_RESTORED",
        "language",
        lang.id,
        {"code": lang.code, "name": lang.name},
        request,
    )
    await db.commit()
    return LanguageResponse.model_validate(lang)
