import time
from collections import deque
from typing import Protocol

import redis

from app.services.context import RequestContext


class RateLimitStore(Protocol):
    async def increment(self, tenant_id: str, api_key_id: str, model: str) -> None: ...


class InMemoryRateLimitStore:
    def __init__(self, limit_per_minute: int) -> None:
        self.limit_per_minute = limit_per_minute
        self.hits: dict[str, deque[float]] = {}

    async def increment(self, tenant_id: str, api_key_id: str, model: str) -> None:
        key = f"{tenant_id}:{api_key_id}:{model}"
        now = time.time()
        window = self.hits.setdefault(key, deque())
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.limit_per_minute:
            raise RuntimeError("rate limit exceeded")
        window.append(now)


class RedisRateLimitStore:
    def __init__(self, redis_url: str, limit_per_minute: int) -> None:
        self.limit_per_minute = limit_per_minute
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)

    async def increment(self, tenant_id: str, api_key_id: str, model: str) -> None:
        key = f"ratelimit:{tenant_id}:{api_key_id}:{model}"
        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, 60)
        if current > self.limit_per_minute:
            raise RuntimeError("rate limit exceeded")


class RateLimitService:
    def __init__(self, store: RateLimitStore) -> None:
        self.store = store

    async def enforce(self, context: RequestContext) -> None:
        context.stage_trace.append("rate_limit")
        await self.store.increment(
            tenant_id=context.tenant_id or "unknown",
            api_key_id=context.api_key_id or "unknown",
            model=context.payload.model,
        )
