"""
Redis client for caching verification results and API performance.
"""

import json
import redis.asyncio as redis
from typing import Optional, Any
from app.config import get_settings

settings = get_settings()

redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


class CacheService:
    """Redis caching layer for verification results and API responses."""

    def __init__(self, client: redis.Redis = None):
        self.client = client or redis_client
        self.default_ttl = settings.CACHE_TTL_SECONDS

    async def get(self, key: str) -> Optional[dict]:
        """Get a cached value by key."""
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None

    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set a cached value with optional TTL."""
        await self.client.set(
            key,
            json.dumps(value, default=str),
            ex=ttl or self.default_ttl,
        )

    async def delete(self, key: str) -> None:
        """Delete a cached value."""
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        return await self.client.exists(key) > 0

    # --- Domain-specific caching methods ---

    async def cache_verification(self, file_hash: str, result: dict) -> None:
        """Cache a verification result for a given file hash."""
        key = f"verify:{file_hash}"
        await self.set(key, result, ttl=self.default_ttl)

    async def get_cached_verification(self, file_hash: str) -> Optional[dict]:
        """Get a cached verification result."""
        key = f"verify:{file_hash}"
        return await self.get(key)

    async def invalidate_verification(self, file_hash: str) -> None:
        """Invalidate a cached verification result."""
        key = f"verify:{file_hash}"
        await self.delete(key)

    async def cache_constituency_list(self, data: list) -> None:
        """Cache constituency listing."""
        await self.set("constituencies:all", data, ttl=600)

    async def get_cached_constituencies(self) -> Optional[list]:
        """Get cached constituency listing."""
        return await self.get("constituencies:all")

    async def increment_counter(self, key: str, ttl: int = 60) -> int:
        """Increment a counter (for rate limiting)."""
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl)
        results = await pipe.execute()
        return results[0]


cache_service = CacheService()
