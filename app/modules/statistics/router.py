from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.shared.redis import get_redis
from app.modules.statistics.service import statistics_service

router = APIRouter(prefix="/portal/statistics", tags=["portal-statistics"])

@router.get("")
async def get_visitor_statistics(
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis)
) -> dict:
    """
    Lấy thống kê số người đang trực tuyến (hoạt động trong 5 phút qua) và tổng lượt truy cập.
    """
    return await statistics_service.get_stats(redis_client, db)
