import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.gallery.schemas import GalleryCreate, GalleryItemResponse, GalleryPaginationResponse, GalleryResponse, GalleryUpdate
from app.modules.gallery.service import gallery_service
from app.core.config import settings

admin_router = APIRouter()
portal_router = APIRouter()


def response(item):
    def media_url(key):
        if not key or key.startswith(("http://", "https://")):
            return key
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{key}"
    return GalleryResponse(
        id=item.id, department_id=item.department_id, cover_object_key=media_url(item.cover_object_key),
        sort_order=item.sort_order, is_active=item.is_active, title=item.title, description=item.description,
        translations=item.translations_map, created_at=item.created_at, updated_at=item.updated_at,
        items=[GalleryItemResponse(id=i.id, media_item_id=i.media_item_id, object_key=media_url(i.object_key),
            thumbnail_key=media_url(i.thumbnail_key), caption=i.caption, alt_text=i.alt_text,
            sort_order=i.sort_order, is_active=i.is_active) for i in item.items if i.is_active]
    )


@admin_router.get("", response_model=GalleryPaginationResponse)
async def list_admin(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
                     department_id: Optional[uuid.UUID] = None, _: UserResponse = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    items, total = await gallery_service.list(db, department_id=department_id, page=page, page_size=page_size)
    return GalleryPaginationResponse(items=[response(i) for i in items], total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


@admin_router.post("", response_model=GalleryResponse, status_code=201)
async def create(payload: GalleryCreate, _: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await gallery_service.save(db, payload)
    await db.commit()
    return response(item)


@admin_router.get("/{gallery_id}", response_model=GalleryResponse)
async def get(gallery_id: uuid.UUID, _: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return response(await gallery_service.get(db, gallery_id))


@admin_router.put("/{gallery_id}", response_model=GalleryResponse)
async def update(gallery_id: uuid.UUID, payload: GalleryUpdate, _: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await gallery_service.update(db, gallery_id, payload)
    await db.commit()
    return response(item)


@admin_router.delete("/{gallery_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(gallery_id: uuid.UUID, _: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await gallery_service.delete(db, gallery_id)
    await db.commit()


@portal_router.get("", response_model=list[GalleryResponse])
async def list_portal(department_id: Optional[uuid.UUID] = None, lang: str = "vi", db: AsyncSession = Depends(get_db)):
    items, _ = await gallery_service.list(db, department_id=department_id, active_only=True, page_size=100, lang=lang)
    return [response(i) for i in items]
