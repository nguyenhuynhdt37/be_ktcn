from typing import Any

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.redis import get_redis

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
) -> dict[str, Any]:
    """
    Check the health of core services (PostgreSQL and Redis).
    """
    postgres_status = "healthy"
    redis_status = "healthy"

    # Ping Postgres
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        postgres_status = f"unhealthy: {str(e)}"

    # Ping Redis
    try:
        await redis_client.ping()
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    is_healthy = postgres_status == "healthy" and redis_status == "healthy"
    status = "healthy" if is_healthy else "unhealthy"

    return {
        "success": is_healthy,
        "status": status,
        "details": {
            "postgres": postgres_status,
            "redis": redis_status,
        },
    }
