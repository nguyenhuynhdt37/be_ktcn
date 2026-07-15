import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.department.models import Department
from app.modules.department.service import department_service
from app.modules.language.models import Language
from app.modules.program.models import (
    Program,
    ProgramCourse,
    ProgramCourseTranslation,
    ProgramDocument,
    ProgramDocumentTranslation,
    ProgramOutcome,
    ProgramOutcomeTranslation,
    ProgramTranslation,
    ProgramVersion,
    ProgramVersionTranslation,
)
from app.modules.program.schemas import (
    ProgramAcademicProfileInput,
    ProgramCreate,
    ProgramUpdate,
)


class ProgramService:
    def apply_translation(self, item: Program, lang: str = "vi") -> Program:
        matched = next((t for t in item.translations if t.language.code == lang), None)
        matched = matched or next(
            (t for t in item.translations if t.language.code == "vi"), None
        )
        matched = matched or (item.translations[0] if item.translations else None)
        from app.core.config import resolve_html_urls

        for field in (
            "name",
            "slug",
            "short_description",
            "description",
            "career_opportunities",
            "admissions_info",
        ):
            val = (
                getattr(matched, field, None)
                if matched
                else ("" if field in ("name", "slug") else None)
            )
            if field in (
                "short_description",
                "description",
                "career_opportunities",
                "admissions_info",
            ):
                val = resolve_html_urls(val)
            setattr(item, field, val)
        item.translations_map = {
            t.language.code: {
                field: (
                    resolve_html_urls(getattr(t, field))
                    if field
                    in (
                        "short_description",
                        "description",
                        "career_opportunities",
                        "admissions_info",
                    )
                    else getattr(t, field)
                )
                for field in (
                    "name",
                    "slug",
                    "short_description",
                    "description",
                    "career_opportunities",
                    "admissions_info",
                )
            }
            for t in item.translations
        }
        return item

    async def list(
        self,
        db: AsyncSession,
        *,
        department_id: uuid.UUID | None = None,
        degree_level: str | None = None,
        search: str | None = None,
        published_only: bool = False,
        page: int = 1,
        page_size: int = 20,
        lang: str = "vi",
    ):
        stmt = select(Program).where(Program.deleted_at.is_(None))
        if department_id:
            stmt = stmt.where(Program.department_id == department_id)
        if degree_level:
            stmt = stmt.where(Program.degree_level == degree_level)
        if published_only:
            stmt = stmt.where(
                Program.is_active.is_(True), Program.is_published.is_(True)
            )
        if search:
            stmt = (
                stmt.join(ProgramTranslation)
                .where(
                    or_(
                        ProgramTranslation.name.ilike(f"%{search}%"),
                        Program.code.ilike(f"%{search}%"),
                    )
                )
                .distinct()
            )
        total = (
            await db.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar() or 0
        stmt = (
            stmt.order_by(Program.sort_order, Program.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list((await db.execute(stmt)).scalars().unique().all())
        return [self.apply_translation(i, lang) for i in items], total

    async def get(
        self, db: AsyncSession, program_id: uuid.UUID, lang: str = "vi"
    ) -> Program:
        item = (
            await db.execute(
                select(Program).where(
                    Program.id == program_id, Program.deleted_at.is_(None)
                )
            )
        ).scalar_one_or_none()
        if not item:
            raise NotFoundException("Không tìm thấy chương trình đào tạo")
        return self.apply_translation(item, lang)

    @staticmethod
    def _translated(translations, lang: str):
        matched = next(
            (item for item in translations if item.language.code == lang), None
        )
        matched = matched or next(
            (item for item in translations if item.language.code == "vi"), None
        )
        return matched or (translations[0] if translations else None)

    def apply_academic_translation(self, item: Program, lang: str = "vi") -> Program:
        self.apply_translation(item, lang)
        for version in item.versions:
            translated = self._translated(version.translations, lang)
            for field in (
                "title",
                "summary",
                "general_objective",
                "career_opportunities",
            ):
                setattr(
                    version,
                    field,
                    getattr(translated, field, None) if translated else None,
                )
            for document in version.documents:
                document_translated = self._translated(document.translations, lang)
                document.title = (
                    getattr(document_translated, "title", "")
                    if document_translated
                    else ""
                )
                document.description = (
                    getattr(document_translated, "description", None)
                    if document_translated
                    else None
                )
            for outcome in version.outcomes:
                outcome_translated = self._translated(outcome.translations, lang)
                outcome.content = (
                    getattr(outcome_translated, "content", "")
                    if outcome_translated
                    else ""
                )
            for course in version.courses:
                course_translated = self._translated(course.translations, lang)
                course.name = (
                    getattr(course_translated, "name", "") if course_translated else ""
                )
        return item

    async def get_by_slug(
        self, db: AsyncSession, slug: str, lang: str = "vi"
    ) -> Program:
        stmt = (
            select(Program)
            .join(ProgramTranslation)
            .where(
                ProgramTranslation.slug == slug,
                Program.deleted_at.is_(None),
                Program.is_active.is_(True),
                Program.is_published.is_(True),
            )
            .options(
                selectinload(Program.versions).selectinload(
                    ProgramVersion.translations
                ),
                selectinload(Program.versions)
                .selectinload(ProgramVersion.documents)
                .selectinload(ProgramDocument.translations),
                selectinload(Program.versions)
                .selectinload(ProgramVersion.outcomes)
                .selectinload(ProgramOutcome.translations),
                selectinload(Program.versions)
                .selectinload(ProgramVersion.courses)
                .selectinload(ProgramCourse.translations),
            )
        )
        item = (await db.execute(stmt)).scalars().unique().one_or_none()
        if not item:
            raise NotFoundException("Không tìm thấy chương trình đào tạo")
        return self.apply_academic_translation(item, lang)

    async def save_academic_profile(  # noqa: C901
        self,
        db: AsyncSession,
        program_id: uuid.UUID,
        data: ProgramAcademicProfileInput,
    ) -> Program:
        item = await self.get(db, program_id)
        languages = {
            language.code: language
            for language in (
                await db.execute(select(Language).where(Language.is_active.is_(True)))
            ).scalars()
        }
        if "vi" not in languages:
            raise BadRequestException("Ngôn ngữ tiếng Việt chưa được cấu hình")

        for version in list(item.versions):
            await db.delete(version)
        await db.flush()

        for version_data in data.versions:
            if "vi" not in version_data.translations:
                raise BadRequestException(
                    f"Phiên bản {version_data.version_year} thiếu nội dung tiếng Việt"
                )
            version = ProgramVersion(
                program_id=item.id,
                version_year=version_data.version_year,
                cohort_code=version_data.cohort_code,
                total_credits=version_data.total_credits,
                is_current=version_data.is_current,
                is_published=version_data.is_published,
                sort_order=version_data.sort_order,
            )
            db.add(version)
            await db.flush()
            for code, translated in version_data.translations.items():
                if code in languages:
                    db.add(
                        ProgramVersionTranslation(
                            version_id=version.id,
                            language_id=languages[code].id,
                            **translated.model_dump(),
                        )
                    )

            for document_data in version_data.documents:
                if "vi" not in document_data.translations:
                    raise BadRequestException(
                        "Tài liệu chương trình thiếu tiêu đề tiếng Việt"
                    )
                document_values = document_data.model_dump(exclude={"translations"})
                document = ProgramDocument(version_id=version.id, **document_values)
                db.add(document)
                await db.flush()
                for code, translated in document_data.translations.items():
                    if code in languages:
                        db.add(
                            ProgramDocumentTranslation(
                                document_id=document.id,
                                language_id=languages[code].id,
                                **translated.model_dump(),
                            )
                        )

            seen_outcomes: set[tuple[str, str]] = set()
            for outcome_data in version_data.outcomes:
                identity = (outcome_data.outcome_type, outcome_data.code.rstrip("."))
                if identity in seen_outcomes:
                    raise BadRequestException(
                        f"Chuẩn đầu ra bị trùng: {outcome_data.code}"
                    )
                seen_outcomes.add(identity)
                if "vi" not in outcome_data.translations:
                    raise BadRequestException(
                        f"{outcome_data.code} thiếu nội dung tiếng Việt"
                    )
                outcome_values = outcome_data.model_dump(exclude={"translations"})
                outcome_values["code"] = outcome_values["code"].rstrip(".")
                outcome = ProgramOutcome(version_id=version.id, **outcome_values)
                db.add(outcome)
                await db.flush()
                for code, translated in outcome_data.translations.items():
                    if code in languages:
                        db.add(
                            ProgramOutcomeTranslation(
                                outcome_id=outcome.id,
                                language_id=languages[code].id,
                                **translated.model_dump(),
                            )
                        )

            seen_courses: set[str] = set()
            for course_data in version_data.courses:
                if course_data.course_code and course_data.course_code in seen_courses:
                    raise BadRequestException(
                        f"Mã học phần bị trùng: {course_data.course_code}"
                    )
                if course_data.course_code:
                    seen_courses.add(course_data.course_code)
                if "vi" not in course_data.translations:
                    label = course_data.course_code or "Dòng chương trình"
                    raise BadRequestException(f"{label} thiếu tên tiếng Việt")
                course_values = course_data.model_dump(exclude={"translations"})
                course = ProgramCourse(version_id=version.id, **course_values)
                db.add(course)
                await db.flush()
                for code, translated in course_data.translations.items():
                    if code in languages:
                        db.add(
                            ProgramCourseTranslation(
                                course_id=course.id,
                                language_id=languages[code].id,
                                **translated.model_dump(),
                            )
                        )

        await db.flush()
        return item

    async def save(  # noqa: C901
        self, db: AsyncSession, data: ProgramCreate, item: Program | None = None
    ) -> Program:
        if "vi" not in data.translations or not data.translations["vi"].name.strip():
            raise BadRequestException("Tên tiếng Việt là bắt buộc")
        if not (
            await db.execute(
                select(Department.id).where(
                    Department.id == data.department_id, Department.deleted_at.is_(None)
                )
            )
        ).scalar():
            raise BadRequestException("Khoa/bộ môn không tồn tại")
        if data.code:
            duplicate = select(Program.id).where(
                Program.code == data.code, Program.deleted_at.is_(None)
            )
            if item:
                duplicate = duplicate.where(Program.id != item.id)
            if (await db.execute(duplicate)).scalar():
                raise BadRequestException("Mã chương trình đã tồn tại")
        if item is None:
            item = Program(translations=[])
            db.add(item)
        for field in (
            "department_id",
            "code",
            "degree_level",
            "duration_years",
            "training_mode",
            "thumbnail_object_key",
            "sort_order",
            "is_active",
            "is_published",
        ):
            setattr(item, field, getattr(data, field))
        await db.flush()
        languages = {
            language.code: language.id
            for language in (
                await db.execute(select(Language).where(Language.is_active.is_(True)))
            ).scalars()
        }
        existing = {t.language.code: t for t in item.translations}
        for code, value in data.translations.items():
            if code not in languages:
                continue
            trans = existing.get(code)
            if trans is None:
                trans = ProgramTranslation(
                    program_id=item.id, language_id=languages[code]
                )
                item.translations.append(trans)
            trans.name = value.name.strip()
            trans.slug = value.slug or department_service.slugify(value.name)
            for field in (
                "short_description",
                "description",
                "career_opportunities",
                "admissions_info",
            ):
                setattr(trans, field, getattr(value, field))
            db.add(trans)
        await db.flush()
        return self.apply_translation(item)

    async def update(
        self, db: AsyncSession, program_id: uuid.UUID, data: ProgramUpdate
    ) -> Program:
        item = await self.get(db, program_id)
        payload = ProgramCreate(
            **{
                field: getattr(data, field)
                if getattr(data, field) is not None
                else getattr(item, field)
                for field in (
                    "department_id",
                    "code",
                    "degree_level",
                    "duration_years",
                    "training_mode",
                    "thumbnail_object_key",
                    "sort_order",
                    "is_active",
                    "is_published",
                )
            },
            translations=data.translations or dict(item.translations_map.items()),
        )
        return await self.save(db, payload, item)

    async def delete(self, db: AsyncSession, program_id: uuid.UUID) -> None:
        item = await self.get(db, program_id)
        item.deleted_at = datetime.now(UTC)
        await db.flush()


program_service = ProgramService()
