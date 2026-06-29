import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.audit.service import log_action
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.media.schemas import (
    FileCopyRequest,
    FolderCreate,
    ItemMove,
    ItemRename,
    MediaItemResponse,
    PresignedUrlResponse,
)
from app.modules.media.service import MediaService

media_router = APIRouter()
media_service = MediaService()


@media_router.post("/folders", response_model=MediaItemResponse)
async def create_folder(
    request: Request,
    payload: FolderCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MediaItemResponse:
    """
    Tạo một thư mục mới.
    Quyền yêu cầu: media.create
    """
    result = await media_service.create_folder(
        db, name=payload.name, parent_id=payload.parent_id
    )
    await log_action(
        db, current_user, "MEDIA_FOLDER_CREATED", "media", result.id,
        {"name": payload.name, "parent_id": str(payload.parent_id) if payload.parent_id else None},
        request,
    )
    await db.commit()
    return result


@media_router.get("", response_model=List[MediaItemResponse])
async def list_directory(
    parent_id: Optional[uuid.UUID] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[MediaItemResponse]:
    """
    Liệt kê nội dung bên trong một thư mục cha (mặc định là thư mục gốc).
    Quyền yêu cầu: media.view
    """
    return await media_service.list_directory(db, parent_id=parent_id)


@media_router.post("/upload", response_model=MediaItemResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    parent_id: Optional[uuid.UUID] = Form(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MediaItemResponse:
    """
    Tải tập tin lên hệ thống.
    Quyền yêu cầu: media.create
    """
    content = await file.read()
    filename = file.filename or "unnamed_file"
    content_type = file.content_type or "application/octet-stream"

    result = await media_service.upload_file(
        db=db,
        file_content=content,
        filename=filename,
        content_type=content_type,
        parent_id=parent_id,
    )
    await log_action(
        db, current_user, "MEDIA_UPLOADED", "media", result.id,
        {"filename": filename, "content_type": content_type, "size": len(content)},
        request,
    )
    await db.commit()
    return result


@media_router.get("/{media_id}/download")
async def download_file(
    media_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Tải tập tin nhị phân về máy.
    Quyền yêu cầu: media.view
    """
    content, filename, content_type = await media_service.get_file_stream(db, media_id)
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@media_router.get("/{media_id}/url")
async def get_url(
    media_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Lấy đường dẫn liên kết công khai trực tiếp của file.
    Quyền yêu cầu: media.view
    """
    url = await media_service.get_url(db, media_id)
    return {"url": url}


@media_router.post("/{media_id}/rename", response_model=MediaItemResponse)
async def rename_item(
    request: Request,
    media_id: uuid.UUID,
    payload: ItemRename,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MediaItemResponse:
    """
    Đổi tên tập tin hoặc thư mục.
    Quyền yêu cầu: media.update
    """
    result = await media_service.rename_item(db, media_id, payload.name)
    await log_action(
        db, current_user, "MEDIA_RENAMED", "media", media_id,
        {"new_name": payload.name}, request,
    )
    await db.commit()
    return result


@media_router.post("/{media_id}/move", response_model=MediaItemResponse)
async def move_item(
    request: Request,
    media_id: uuid.UUID,
    payload: ItemMove,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MediaItemResponse:
    """
    Di chuyển tập tin hoặc thư mục sang một thư mục cha khác.
    Quyền yêu cầu: media.update
    """
    result = await media_service.move_item(db, media_id, payload.parent_id)
    await log_action(
        db, current_user, "MEDIA_MOVED", "media", media_id,
        {"new_parent_id": str(payload.parent_id) if payload.parent_id else None}, request,
    )
    await db.commit()
    return result


@media_router.post("/{media_id}/copy", response_model=MediaItemResponse)
async def copy_file(
    request: Request,
    media_id: uuid.UUID,
    payload: FileCopyRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MediaItemResponse:
    """
    Sao chép tập tin sang thư mục cha khác.
    Quyền yêu cầu: media.update
    """
    result = await media_service.copy_file(db, media_id, payload.dest_parent_id)
    await log_action(
        db, current_user, "MEDIA_COPIED", "media", media_id,
        {"dest_parent_id": str(payload.dest_parent_id) if payload.dest_parent_id else None}, request,
    )
    await db.commit()
    return result


@media_router.delete("/{media_id}")
async def delete_item(
    request: Request,
    media_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Xóa tập tin hoặc thư mục.
    Quyền yêu cầu: media.delete
    """
    await media_service.delete_item(db, media_id)
    await log_action(db, current_user, "MEDIA_DELETED", "media", media_id, None, request)
    await db.commit()
    return {"success": True}


@media_router.post("/presigned-upload", response_model=PresignedUrlResponse)
async def generate_presigned_upload(
    filename: str,
    content_type: str,
    expires_in: int = 3600,
    current_user: UserResponse = Depends(get_current_user),
) -> PresignedUrlResponse:
    """
    Sinh S3 presigned post URL để client tự tải file lên MinIO một cách bảo mật.
    Quyền yêu cầu: media.create
    """
    data = await media_service.generate_presigned_upload_url(
        filename=filename, content_type=content_type, expires_in=expires_in
    )
    return PresignedUrlResponse(**data)


@media_router.get("/{media_id}/presigned-download")
async def generate_presigned_download(
    media_id: uuid.UUID,
    expires_in: int = 3600,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Sinh đường dẫn tải xuống có thời hạn (presigned download URL) bảo mật cho file.
    Quyền yêu cầu: media.view
    """
    url = await media_service.generate_presigned_download_url(
        db, media_id, expires_in=expires_in
    )
    return {"url": url}
