from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from loguru import logger

from app.core.config import settings

# Global Redis connection pool
redis_pool: aioredis.ConnectionPool | None = None


def init_redis() -> None:
    """
    Initializes the Redis connection pool.
    """
    global redis_pool
    logger.info("Initializing Redis connection pool...")
    redis_pool = aioredis.ConnectionPool.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=50,
    )


async def close_redis() -> None:
    """
    Closes the Redis connection pool.
    """
    global redis_pool
    if redis_pool:
        logger.info("Closing Redis connection pool...")
        await redis_pool.disconnect()
        redis_pool = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Dependency injection provider for Redis async clients.
    """
    global redis_pool
    if redis_pool is None:
        init_redis()

    client = aioredis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()
