from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.banner.models import BannerPosition
from app.modules.banner.schemas.common import BannerResponse
from app.modules.banner.service import banner_service

portal_router = APIRouter()


@portal_router.get("", response_model=list[BannerResponse])
async def list_banners_portal(
    position: Optional[BannerPosition] = Query(default=None, description="Lọc theo vị trí hiển thị"),
    db: AsyncSession = Depends(get_db),
) -> list[BannerResponse]:
    """
    Lấy danh sách các banner đang hiệu lực hiển thị ở Portal (Public - Không cần đăng nhập).
    Trả về mảng danh sách được sắp xếp theo sort_order tăng dần.
    """
    banners = await banner_service.list_banners_portal(db, position=position)
    return [BannerResponse.model_validate(b) for b in banners]
