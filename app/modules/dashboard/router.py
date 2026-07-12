from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.shared.redis import get_redis
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.dashboard.schemas import DashboardResponse
from app.modules.dashboard.service import dashboard_service

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
) -> DashboardResponse:
    """
    Lấy toàn bộ thống kê tổng quan hệ thống cho Admin Dashboard.
    Bao gồm: visitors, articles, users, consultations, content, logins,
    top articles, và hoạt động gần đây.
    """
    return await dashboard_service.get_dashboard(db, redis_client)
