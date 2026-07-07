"""
Redis-backed session memory (I-04).
"""
import json
import logging
from typing import Optional, Dict

import redis.asyncio as aioredis

from app.domain.chat import SessionStorePort
from app.core.config import settings


class RedisSessionStoreAdapter(SessionStorePort):
    def __init__(self, redis_url: str = ""):
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self):
        if self._redis is None:
            self._redis = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            )
        return self._redis

    async def get_session(self, session_id: str) -> Optional[Dict]:
        try:
            redis = await self._get_redis()
            raw = await redis.get(f"session:{session_id}")
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as e:
            logging.warning(f"RedisSessionStore: get failed {e}")
            return None

    async def set_session(self, session_id: str, data: Dict, ttl: int = 0) -> None:
        if ttl == 0:
            ttl = settings.SESSION_TTL
        try:
            redis = await self._get_redis()
            await redis.setex(f"session:{session_id}", ttl, json.dumps(data))
        except Exception as e:
            logging.warning(f"RedisSessionStore: set failed {e}")

    async def delete_session(self, session_id: str) -> None:
        try:
            redis = await self._get_redis()
            await redis.delete(f"session:{session_id}")
        except Exception as e:
            logging.warning(f"RedisSessionStore: delete failed {e}")

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()
            self._redis = None
