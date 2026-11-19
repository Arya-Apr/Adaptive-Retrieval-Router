from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError
from .config import settings
from .models import RetrievalDecision


class RouteCache:
    def __init__(self):
        self.redis = Redis.from_url(settings.redis_url, socket_connect_timeout=.3, socket_timeout=.3) if settings.redis_url else None

    async def get(self, key: str):
        if self.redis:
            try:
                raw = await self.redis.get(key)
                return RetrievalDecision.model_validate_json(raw) if raw else None
            except (RedisError, ValidationError):
                pass
        return None

    async def set(self, key: str, decision: RetrievalDecision):
        if self.redis:
            try:
                await self.redis.set(key, decision.model_dump_json(), ex=settings.route_cache_ttl_seconds)
            except RedisError:
                pass
