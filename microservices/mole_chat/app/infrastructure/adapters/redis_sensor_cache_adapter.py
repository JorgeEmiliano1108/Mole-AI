"""
Redis adapter with optional mTLS support (ETSI EN 303 645).
Uses the official redis.asyncio client.
"""
import logging
import os
from typing import Optional

import redis.asyncio as aioredis

from app.domain.chat import SensorCachePort
from app.core.config import settings


class RedisSensorCacheAdapter(SensorCachePort):
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
        self._tls_kwargs = self._build_tls_kwargs()

    @staticmethod
    def _build_tls_kwargs() -> dict:
        kwargs = {}
        cert_path = settings.TLS_CERT_PATH
        key_path = settings.TLS_KEY_PATH
        ca_path = settings.TLS_CA_PATH
        if cert_path and os.path.exists(cert_path):
            kwargs["ssl_certfile"] = cert_path
        if key_path and os.path.exists(key_path):
            kwargs["ssl_keyfile"] = key_path
        if ca_path and os.path.exists(ca_path):
            kwargs["ssl_ca_certs"] = ca_path
        if kwargs:
            # redis.asyncio expects ssl=True when using TLS
            kwargs["ssl"] = True
        return kwargs

    async def _get_redis(self):
        if self._redis is None:
            self._redis = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                **self._tls_kwargs,
            )
        return self._redis

    async def get_context(self, user_id: str):
        try:
            redis = await self._get_redis()
            key = f"mqtt:context:{user_id}"
            context = await redis.get(key)
            if context is None:
                logging.warning(f"[RedisSensorCacheAdapter] Context key '{key}' not found. Using fallback.")
                return {}
            return context
        except (ConnectionError, OSError, TimeoutError) as e:
            logging.warning(f"[RedisSensorCacheAdapter] Redis connection/timeout: {e}. Returning empty context.")
            return {}
        except Exception as e:
            logging.warning(f"[RedisSensorCacheAdapter] Redis unavailable: {e}. Using fallback.")
            return {}

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()
            self._redis = None
