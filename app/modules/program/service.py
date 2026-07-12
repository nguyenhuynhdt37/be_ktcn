import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.department.models import Department
from app.modules.department.service import department_service
from app.modules.language.models import Language
from app.modules.program.models import Program, ProgramTranslation
from app.modules.program.schemas import ProgramCreate, ProgramUpdate


class ProgramService:
    def apply_translation(self, item: Program, lang: str = "vi") -> Program:
        matched = next((t for t in item.translations if t.language.code == lang), None)
        matched = matched or next((t for t in item.translations if t.language.code == "vi"), None)
        matched = matched or (item.translations[0] if item.translations else None)
        from app.core.config import resolve_html_urls
        for field in ("name", "slug", "short_description", "description", "career_opportunities", "admissions_info"):
            val = getattr(matched, field, None) if matched else ("" if field in ("name", "slug") else None)
            if field in ("short_description", "description", "career_opportunities", "admissions_info"):
                val = resolve_html_urls(val)
            setattr(item, field, val)
        item.translations_map = {
            t.language.code: {
                field: (resolve_html_urls(getattr(t, field)) if field in ("short_description", "description", "career_opportunities", "admissions_info") else getattr(t, field))
                for field in ("name", "slug", "short_description", "description", "career_opportunities", "admissions_info")
            }
            for t in item.translations
        }
        return item

    async def list(self, db: AsyncSession, *, department_id: Optional[uuid.UUID] = None,
                   search: Optional[str] = None, published_only: bool = False,
                   page: int = 1, page_size: int = 20, lang: str = "vi"):
        stmt = select(Program).where(Program.deleted_at.is_(None))
        if department_id:
            stmt = stmt.where(Program.department_id == department_id)
        if published_only:
            stmt = stmt.where(Program.is_active.is_(True), Program.is_published.is_(True))
        if search:
            stmt = stmt.join(ProgramTranslation).where(or_(ProgramTranslation.name.ilike(f"%{search}%"), Program.code.ilike(f"%{search}%"))).distinct()
        total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
        stmt = stmt.order_by(Program.sort_order, Program.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list((await db.execute(stmt)).scalars().unique().all())
        return [self.apply_translation(i, lang) for i in items], total

    async def get(self, db: AsyncSession, program_id: uuid.UUID, lang: str = "vi") -> Program:
        item = (await db.execute(select(Program).where(Program.id == program_id, Program.deleted_at.is_(None)))).scalar_one_or_none()
        if not item:
            raise NotFoundException("Không tìm thấy chương trình đào tạo")
        return self.apply_translation(item, lang)

    async def save(self, db: AsyncSession, data: ProgramCreate, item: Optional[Program] = None) -> Program:
        if "vi" not in data.translations or not data.translations["vi"].name.strip():
            raise BadRequestException("Tên tiếng Việt là bắt buộc")
        if not (await db.execute(select(Department.id).where(Department.id == data.department_id, Department.deleted_at.is_(None)))).scalar():
            raise BadRequestException("Khoa/bộ môn không tồn tại")
        if data.code:
            duplicate = select(Program.id).where(Program.code == data.code, Program.deleted_at.is_(None))
            if item:
                duplicate = duplicate.where(Program.id != item.id)
            if (await db.execute(duplicate)).scalar():
                raise BadRequestException("Mã chương trình đã tồn tại")
        if item is None:
            item = Program(translations=[])
            db.add(item)
        for field in ("department_id", "code", "degree_level", "duration_years", "training_mode", "thumbnail_object_key", "sort_order", "is_active", "is_published"):
            setattr(item, field, getattr(data, field))
        await db.flush()
        languages = {l.code: l.id for l in (await db.execute(select(Language).where(Language.is_active.is_(True)))).scalars()}
        existing = {t.language.code: t for t in item.translations}
        for code, value in data.translations.items():
            if code not in languages:
                continue
            trans = existing.get(code)
            if trans is None:
                trans = ProgramTranslation(program_id=item.id, language_id=languages[code])
                item.translations.append(trans)
            trans.name = value.name.strip()
            trans.slug = value.slug or department_service.slugify(value.name)
            for field in ("short_description", "description", "career_opportunities", "admissions_info"):
                setattr(trans, field, getattr(value, field))
            db.add(trans)
        await db.flush()
        return self.apply_translation(item)

    async def update(self, db: AsyncSession, program_id: uuid.UUID, data: ProgramUpdate) -> Program:
        item = await self.get(db, program_id)
        payload = ProgramCreate(
            **{field: getattr(data, field) if getattr(data, field) is not None else getattr(item, field)
               for field in ("department_id", "code", "degree_level", "duration_years", "training_mode", "thumbnail_object_key", "sort_order", "is_active", "is_published")},
            translations=data.translations or {code: value for code, value in item.translations_map.items()}
        )
        return await self.save(db, payload, item)

    async def delete(self, db: AsyncSession, program_id: uuid.UUID) -> None:
        item = await self.get(db, program_id)
        item.deleted_at = datetime.now(UTC)
        await db.flush()


program_service = ProgramService()
