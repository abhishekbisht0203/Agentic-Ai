"""Redis cache service."""

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-based caching service with async support."""

    _client: redis.Redis | None = None
    is_connected: bool = False

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    @classmethod
    async def initialize(cls) -> None:
        """Initialize the global Redis connection."""
        try:
            cls._client = redis.from_url(
                settings.redis.redis_url,
                decode_responses=True,
            )
            await cls._client.ping()
            cls.is_connected = True
            logger.info("Redis connection established")
        except Exception as exc:
            logger.warning("Redis connection failed: %s", exc)
            cls.is_connected = False

    @classmethod
    async def close(cls) -> None:
        """Close the global Redis connection."""
        if cls._client:
            try:
                await cls._client.close()
            except Exception:
                pass
            cls._client = None
            cls.is_connected = False

    async def get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                settings.redis.redis_url,
                decode_responses=True,
            )
        return self._client

    async def get(self, key: str) -> Any | None:
        client = await self.get_client()
        value = await client.get(key)
        if value:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        client = await self.get_client()
        if isinstance(value, (dict, list)):
            value = json.dumps(value, default=str)
        return await client.setex(key, ttl, value)

    async def delete(self, key: str) -> bool:
        client = await self.get_client()
        return await client.delete(key) > 0

    async def exists(self, key: str) -> bool:
        client = await self.get_client()
        return await client.exists(key) > 0

    async def increment(self, key: str, amount: int = 1) -> int:
        client = await self.get_client()
        return await client.incr(key, amount)

    async def set_hash(self, key: str, mapping: dict[str, Any]) -> None:
        client = await self.get_client()
        await client.hset(key, mapping={k: json.dumps(v, default=str) for k, v in mapping.items()})

    async def get_hash(self, key: str) -> dict[str, Any]:
        client = await self.get_client()
        data = await client.hgetall(key)
        return {k: json.loads(v) for k, v in data.items()} if data else {}

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
