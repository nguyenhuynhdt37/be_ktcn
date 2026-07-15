import uuid

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.program.schemas import (
    ProgramAcademicProfileInput,
    ProgramCourseResponse,
    ProgramCreate,
    ProgramDetailResponse,
    ProgramDocumentResponse,
    ProgramOutcomeResponse,
    ProgramPaginationResponse,
    ProgramResponse,
    ProgramUpdate,
    ProgramVersionResponse,
)
from app.modules.program.service import program_service

admin_router = APIRouter()
portal_router = APIRouter()


def response(item):
    data = {
        field: getattr(item, field, definition.default)
        for field, definition in ProgramResponse.model_fields.items()
        if field != "translations"
    }
    data["translations"] = getattr(item, "translations_map", {})
    key = data.get("thumbnail_object_key")
    if key and not key.startswith(("http://", "https://")):
        protocol = "https" if settings.MINIO_SECURE else "http"
        data["thumbnail_object_key"] = (
            f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{key}"
        )
    return ProgramResponse(**data)


def _file_url(object_key: str | None) -> str | None:
    if not object_key:
        return None
    if object_key.startswith(("http://", "https://", "/")):
        return object_key
    return f"{settings.API_V1_STR}/portal/media/file/{object_key}"


def detail_response(item, *, published_only: bool = False) -> ProgramDetailResponse:
    base = response(item).model_dump()
    versions = []
    for version in item.versions:
        if published_only and not version.is_published:
            continue
        documents = [
            ProgramDocumentResponse(
                id=document.id,
                document_type=document.document_type,
                title=getattr(document, "title", ""),
                description=getattr(document, "description", None),
                source_url=document.source_url,
                file_url=_file_url(document.object_key) or document.source_url,
                mime_type=document.mime_type,
                file_size=document.file_size,
                page_count=document.page_count,
                checksum_sha256=document.checksum_sha256,
                sort_order=document.sort_order,
            )
            for document in version.documents
        ]
        outcome_responses = [
            ProgramOutcomeResponse(
                id=outcome.id,
                code=outcome.code,
                outcome_type=outcome.outcome_type,
                parent_code=outcome.parent_code,
                content=getattr(outcome, "content", ""),
                sort_order=outcome.sort_order,
            )
            for outcome in version.outcomes
        ]
        courses = [
            ProgramCourseResponse(
                id=course.id,
                course_code=course.course_code,
                row_type=course.row_type,
                name=getattr(course, "name", ""),
                credits=float(course.credits) if course.credits is not None else None,
                credits_text=course.credits_text,
                semester=course.semester,
                knowledge_block=course.knowledge_block,
                course_type=course.course_type,
                managing_unit=course.managing_unit,
                sort_order=course.sort_order,
            )
            for course in version.courses
        ]
        versions.append(
            ProgramVersionResponse(
                id=version.id,
                version_year=version.version_year,
                cohort_code=version.cohort_code,
                total_credits=float(version.total_credits)
                if version.total_credits is not None
                else None,
                is_current=version.is_current,
                is_published=version.is_published,
                sort_order=version.sort_order,
                title=getattr(version, "title", ""),
                summary=getattr(version, "summary", None),
                general_objective=getattr(version, "general_objective", None),
                career_opportunities=getattr(version, "career_opportunities", None),
                documents=documents,
                objectives=[
                    item
                    for item in outcome_responses
                    if item.outcome_type == "objective"
                ],
                learning_outcomes=[
                    item
                    for item in outcome_responses
                    if item.outcome_type == "learning_outcome"
                ],
                courses=courses,
            )
        )
    return ProgramDetailResponse(**base, versions=versions)


def academic_profile_response(item) -> ProgramAcademicProfileInput:
    def translations(items, *fields: str) -> dict[str, dict]:
        return {
            translation.language.code: {
                field: getattr(translation, field) for field in fields
            }
            for translation in items
        }

    return ProgramAcademicProfileInput(
        versions=[
            {
                "version_year": version.version_year,
                "cohort_code": version.cohort_code,
                "total_credits": float(version.total_credits)
                if version.total_credits is not None
                else None,
                "is_current": version.is_current,
                "is_published": version.is_published,
                "sort_order": version.sort_order,
                "translations": translations(
                    version.translations,
                    "title",
                    "summary",
                    "general_objective",
                    "career_opportunities",
                ),
                "documents": [
                    {
                        "document_type": document.document_type,
                        "source_url": document.source_url,
                        "object_key": document.object_key,
                        "mime_type": document.mime_type,
                        "file_size": document.file_size,
                        "page_count": document.page_count,
                        "checksum_sha256": document.checksum_sha256,
                        "sort_order": document.sort_order,
                        "translations": translations(
                            document.translations, "title", "description"
                        ),
                    }
                    for document in version.documents
                ],
                "outcomes": [
                    {
                        "code": outcome.code,
                        "outcome_type": outcome.outcome_type,
                        "parent_code": outcome.parent_code,
                        "sort_order": outcome.sort_order,
                        "translations": translations(outcome.translations, "content"),
                    }
                    for outcome in version.outcomes
                ],
                "courses": [
                    {
                        "course_code": course.course_code,
                        "row_type": course.row_type,
                        "credits": float(course.credits)
                        if course.credits is not None
                        else None,
                        "credits_text": course.credits_text,
                        "semester": course.semester,
                        "knowledge_block": course.knowledge_block,
                        "course_type": course.course_type,
                        "managing_unit": course.managing_unit,
                        "sort_order": course.sort_order,
                        "translations": translations(course.translations, "name"),
                    }
                    for course in version.courses
                ],
            }
            for version in item.versions
        ]
    )


@admin_router.get("", response_model=ProgramPaginationResponse)
async def list_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    department_id: uuid.UUID | None = None,
    degree_level: str | None = Query(None, pattern="^(bachelor|master|doctorate)$"),
    search: str | None = None,
    _: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await program_service.list(
        db,
        department_id=department_id,
        degree_level=degree_level,
        search=search,
        page=page,
        page_size=page_size,
    )
    return ProgramPaginationResponse(
        items=[response(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@admin_router.post("", response_model=ProgramResponse, status_code=201)
async def create(
    payload: ProgramCreate,
    _: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await program_service.save(db, payload)
    await db.commit()
    return response(item)


@admin_router.get("/{program_id}", response_model=ProgramResponse)
async def get(
    program_id: uuid.UUID,
    _: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return response(await program_service.get(db, program_id))


@admin_router.put("/{program_id}", response_model=ProgramResponse)
async def update(
    program_id: uuid.UUID,
    payload: ProgramUpdate,
    _: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await program_service.update(db, program_id, payload)
    await db.commit()
    return response(item)


@admin_router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    program_id: uuid.UUID,
    _: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await program_service.delete(db, program_id)
    await db.commit()


@admin_router.get(
    "/{program_id}/academic-profile", response_model=ProgramAcademicProfileInput
)
async def get_academic_profile(
    program_id: uuid.UUID,
    _: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await program_service.get(db, program_id)
    return academic_profile_response(item)


@admin_router.put(
    "/{program_id}/academic-profile", response_model=ProgramDetailResponse
)
async def replace_academic_profile(
    program_id: uuid.UUID,
    payload: ProgramAcademicProfileInput,
    _: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await program_service.save_academic_profile(db, program_id, payload)
    await db.commit()
    item = await program_service.get(db, program_id)
    return detail_response(program_service.apply_academic_translation(item))


@portal_router.get("", response_model=list[ProgramResponse])
async def list_portal(
    department_id: uuid.UUID | None = None,
    degree_level: str | None = Query(None, pattern="^(bachelor|master|doctorate)$"),
    lang: str = Query("vi"),
    accept_language: str | None = Header(None, alias="Accept-Language"),
    db: AsyncSession = Depends(get_db),
):
    selected = lang or ((accept_language or "vi").split(",")[0].split("-")[0])
    items, _ = await program_service.list(
        db,
        department_id=department_id,
        degree_level=degree_level,
        published_only=True,
        page_size=200,
        lang=selected,
    )
    return [response(i) for i in items]


@portal_router.get("/{slug}", response_model=ProgramDetailResponse)
async def get_portal_detail(
    slug: str,
    lang: str = Query("vi"),
    accept_language: str | None = Header(None, alias="Accept-Language"),
    db: AsyncSession = Depends(get_db),
):
    selected = lang or ((accept_language or "vi").split(",")[0].split("-")[0])
    item = await program_service.get_by_slug(db, slug, selected)
    return detail_response(item, published_only=True)
