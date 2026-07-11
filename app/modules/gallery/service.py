import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.department.models import Department
from app.modules.gallery.models import DepartmentGallery, DepartmentGalleryItem, DepartmentGalleryTranslation
from app.modules.gallery.schemas import GalleryCreate, GalleryUpdate
from app.modules.language.models import Language
from app.modules.media.models import MediaItem


class GalleryService:
    def apply_translation(self, gallery: DepartmentGallery, lang: str = "vi") -> DepartmentGallery:
        matched = next((t for t in gallery.translations if t.language.code == lang), None)
        matched = matched or next((t for t in gallery.translations if t.language.code == "vi"), None)
        matched = matched or (gallery.translations[0] if gallery.translations else None)
        gallery.title = matched.title if matched else ""
        gallery.description = matched.description if matched else None
        gallery.translations_map = {t.language.code: {"title": t.title, "description": t.description} for t in gallery.translations}
        for item in gallery.items:
            item.object_key = item.media_item.object_key if item.media_item else None
            item.thumbnail_key = item.media_item.thumbnail_key if item.media_item else None
        return gallery

    async def list(self, db: AsyncSession, *, department_id: Optional[uuid.UUID] = None,
                   active_only: bool = False, page: int = 1, page_size: int = 20, lang: str = "vi"):
        stmt = select(DepartmentGallery).where(DepartmentGallery.deleted_at.is_(None))
        if department_id:
            stmt = stmt.where(DepartmentGallery.department_id == department_id)
        if active_only:
            stmt = stmt.where(DepartmentGallery.is_active.is_(True))
        total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
        stmt = stmt.order_by(DepartmentGallery.sort_order, DepartmentGallery.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        galleries = list((await db.execute(stmt)).scalars().unique().all())
        return [self.apply_translation(g, lang) for g in galleries], total

    async def get(self, db: AsyncSession, gallery_id: uuid.UUID, lang: str = "vi") -> DepartmentGallery:
        item = (await db.execute(select(DepartmentGallery).where(DepartmentGallery.id == gallery_id, DepartmentGallery.deleted_at.is_(None)))).scalar_one_or_none()
        if not item:
            raise NotFoundException("Không tìm thấy thư viện ảnh")
        return self.apply_translation(item, lang)

    async def save(self, db: AsyncSession, data: GalleryCreate, gallery: Optional[DepartmentGallery] = None) -> DepartmentGallery:
        if "vi" not in data.translations or not data.translations["vi"].title.strip():
            raise BadRequestException("Tên album tiếng Việt là bắt buộc")
        if not (await db.execute(select(Department.id).where(Department.id == data.department_id, Department.deleted_at.is_(None)))).scalar():
            raise BadRequestException("Khoa/bộ môn không tồn tại")
        media_ids = [i.media_item_id for i in data.items]
        media_map = {}
        if media_ids:
            media = list((await db.execute(select(MediaItem).where(MediaItem.id.in_(media_ids), MediaItem.is_folder.is_(False)))).scalars())
            media_map = {item.id: item for item in media}
            if len(media_map) != len(set(media_ids)):
                raise BadRequestException("Một hoặc nhiều ảnh không tồn tại")
        if gallery is None:
            gallery = DepartmentGallery(translations=[], items=[])
            db.add(gallery)
        for field in ("department_id", "cover_object_key", "sort_order", "is_active"):
            setattr(gallery, field, getattr(data, field))
        await db.flush()
        languages = {l.code: l.id for l in (await db.execute(select(Language).where(Language.is_active.is_(True)))).scalars()}
        existing = {t.language.code: t for t in gallery.translations}
        for code, value in data.translations.items():
            if code not in languages:
                continue
            trans = existing.get(code)
            if trans is None:
                trans = DepartmentGalleryTranslation(gallery_id=gallery.id, language_id=languages[code])
                gallery.translations.append(trans)
            trans.title, trans.description = value.title.strip(), value.description
            db.add(trans)
        gallery.items.clear()
        await db.flush()
        for value in data.items:
            gallery.items.append(DepartmentGalleryItem(gallery_id=gallery.id, media_item=media_map[value.media_item_id], **value.model_dump()))
        await db.flush()
        return self.apply_translation(gallery)

    async def update(self, db: AsyncSession, gallery_id: uuid.UUID, data: GalleryUpdate) -> DepartmentGallery:
        item = await self.get(db, gallery_id)
        payload = GalleryCreate(
            department_id=data.department_id or item.department_id,
            cover_object_key=data.cover_object_key if data.cover_object_key is not None else item.cover_object_key,
            sort_order=data.sort_order if data.sort_order is not None else item.sort_order,
            is_active=data.is_active if data.is_active is not None else item.is_active,
            translations=data.translations or item.translations_map,
            items=data.items if data.items is not None else [
                {"media_item_id": i.media_item_id, "caption": i.caption, "alt_text": i.alt_text, "sort_order": i.sort_order, "is_active": i.is_active}
                for i in item.items
            ],
        )
        return await self.save(db, payload, item)

    async def delete(self, db: AsyncSession, gallery_id: uuid.UUID) -> None:
        item = await self.get(db, gallery_id)
        item.deleted_at = datetime.now(UTC)
        await db.flush()


gallery_service = GalleryService()
