import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.program.schemas import ProgramCreate, ProgramPaginationResponse, ProgramResponse, ProgramUpdate
from app.modules.program.service import program_service
from app.core.config import settings

admin_router = APIRouter()
portal_router = APIRouter()


def response(item):
    data = ProgramResponse.model_validate(item).model_dump()
    data["translations"] = getattr(item, "translations_map", {})
    key = data.get("thumbnail_object_key")
    if key and not key.startswith(("http://", "https://")):
        protocol = "https" if settings.MINIO_SECURE else "http"
        data["thumbnail_object_key"] = f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{key}"
    return ProgramResponse(**data)


@admin_router.get("", response_model=ProgramPaginationResponse)
async def list_admin(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
                     department_id: Optional[uuid.UUID] = None, search: Optional[str] = None,
                     _: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items, total = await program_service.list(db, department_id=department_id, search=search, page=page, page_size=page_size)
    return ProgramPaginationResponse(items=[response(i) for i in items], total=total, page=page, page_size=page_size, total_pages=(total + page_size - 1) // page_size)


@admin_router.post("", response_model=ProgramResponse, status_code=201)
async def create(payload: ProgramCreate, _: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await program_service.save(db, payload)
    await db.commit()
    return response(item)


@admin_router.get("/{program_id}", response_model=ProgramResponse)
async def get(program_id: uuid.UUID, _: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return response(await program_service.get(db, program_id))


@admin_router.put("/{program_id}", response_model=ProgramResponse)
async def update(program_id: uuid.UUID, payload: ProgramUpdate, _: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await program_service.update(db, program_id, payload)
    await db.commit()
    return response(item)


@admin_router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(program_id: uuid.UUID, _: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await program_service.delete(db, program_id)
    await db.commit()


@portal_router.get("", response_model=list[ProgramResponse])
async def list_portal(department_id: Optional[uuid.UUID] = None, lang: str = Query("vi"),
                      accept_language: Optional[str] = Header(None, alias="Accept-Language"), db: AsyncSession = Depends(get_db)):
    selected = lang or ((accept_language or "vi").split(",")[0].split("-")[0])
    items, _ = await program_service.list(db, department_id=department_id, published_only=True, page_size=200, lang=selected)
    return [response(i) for i in items]
