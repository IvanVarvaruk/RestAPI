from fastapi import Depends, Request
from redis.asyncio import Redis

from api.dependencies import get_current_user
from api.rate_limiter import rate_limit
from core.redis_client import get_redis


async def rate_limit_authenticated(
    request: Request,
    current_user=Depends(get_current_user),
    redis_client: Redis = Depends(get_redis),
) -> None:
    await rate_limit(request=request, redis_client=redis_client, user_id=str(current_user.id))

