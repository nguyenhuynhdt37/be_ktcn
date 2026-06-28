from loguru import logger
import redis.asyncio as aioredis


async def check_rate_limit(
    redis_client: aioredis.Redis,
    key: str,
    max_attempts: int = 5,
    window_seconds: int = 60,
) -> tuple[bool, int, int]:
    """
    Checks if the given key has exceeded the rate limit.

    Returns:
        (allowed, remaining, retry_after_seconds)
        - allowed: True if the request is within the limit.
        - remaining: Number of attempts left in the current window.
        - retry_after: Seconds until the window resets (0 if allowed).
    """
    try:
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, window_seconds)

        ttl = await redis_client.ttl(key)
        if ttl < 0:
            ttl = window_seconds

        remaining = max(0, max_attempts - current)
        allowed = current <= max_attempts

        return allowed, remaining, 0 if allowed else ttl
    except Exception as e:
        # If Redis is down, fail open (allow the request) to avoid blocking auth
        logger.warning(f"Rate limiter Redis error (fail-open): {e}")
        return True, max_attempts, 0
