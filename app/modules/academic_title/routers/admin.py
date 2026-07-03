from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.academic_title.schemas.admin import AcademicTitleAdminResponse
from app.modules.academic_title.service import AcademicTitleService

admin_router = APIRouter()

academic_title_service = AcademicTitleService()


@admin_router.get("", response_model=List[AcademicTitleAdminResponse])
async def list_academic_titles_admin(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lấy toàn bộ danh sách Học hàm cho Admin quản trị."""
    return await academic_title_service.list_academic_titles(db, lang="vi")
