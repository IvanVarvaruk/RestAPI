import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from core.redis_client import get_redis

RATE_LIMITS: dict[str, tuple[int, int]] = {
    "anonymous": (2, 60),
    "authenticated": (10, 60),
}


async def rate_limit(request: Request, redis_client: Redis, user_id: Optional[str]) -> None:
    identity = user_id or (request.client.host if request.client else "unknown")
    limit_type = "authenticated" if user_id else "anonymous"
    limit, period = RATE_LIMITS[limit_type]

    endpoint = request.url.path
    key = f"rate_limit:{limit_type}:{identity}:{endpoint}"

    now = int(time.time())
    window_start = now - period

    await redis_client.zremrangebyscore(key, min=0, max=window_start)
    request_count = await redis_client.zcard(key)

    if request_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )

    await redis_client.zadd(key, {str(now): now})
    await redis_client.expire(key, period)


async def rate_limit_anonymous(
    request: Request,
    redis_client: Redis = Depends(get_redis),
) -> None:
    await rate_limit(request=request, redis_client=redis_client, user_id=None)

