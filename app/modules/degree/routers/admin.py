from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.degree.schemas import DegreeAdminResponse
from app.modules.degree.service import DegreeService

admin_router = APIRouter()
degree_service = DegreeService()


@admin_router.get("", response_model=List[DegreeAdminResponse])
async def list_degrees_admin(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Lấy toàn bộ danh sách Học vị cho Admin quản trị."""
    return await degree_service.list_degrees(db, lang="vi")
