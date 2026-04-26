import logging
from app.domain.chat import SensorCachePort
from app.domain.exceptions import SensorCacheUnavailable

# aioredis may not be installed in some test environments; provide a lightweight
# stub so tests can monkeypatch the module at runtime. Real deployments should
# install the `aioredis` package and the stub will be unused.
try:
    import aioredis  # type: ignore
except Exception:  # pragma: no cover - test-time fallback
    class _AioredisStub:
        @staticmethod
        async def from_url(url, decode_responses=True):
            raise ConnectionError("aioredis not installed")

    aioredis = _AioredisStub()


class RedisSensorCacheAdapter(SensorCachePort):
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            # may raise if aioredis stub triggers an error
            self._redis = await aioredis.from_url(self.redis_url, decode_responses=True)
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
        except (ConnectionError, TimeoutError) as e:
            # Explicitly handle common redis/connectivity exceptions and fallback silently
            logging.warning(f"[RedisSensorCacheAdapter] Redis connection/timeout: {e}. Returning empty context.")
            return {}
        except Exception as e:
            logging.warning(f"[RedisSensorCacheAdapter] Redis unavailable: {e}. Using fallback.")
            return {}  # Fallback: contexto vacío
