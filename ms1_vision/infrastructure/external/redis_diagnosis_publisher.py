import json
from typing import Any, Dict
import redis.asyncio as aioredis


class RedisDiagnosisPublisher:
    def __init__(self, redis_url: str, channel_prefix: str = "mole:diagnosis:") -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self._channel_prefix = channel_prefix

    async def publish_diagnostic(self, diagnostic: Dict[str, Any]) -> None:
        # channel: mole:diagnosis:{plant_id}
        plant_id = diagnostic.get("plant_id") or "unknown"
        channel = f"{self._channel_prefix}{plant_id}"
        payload = json.dumps(diagnostic, default=str)
        try:
            await self._redis.publish(channel, payload)
        except Exception:
            # best-effort
            return

    async def close(self) -> None:
        try:
            await self._redis.close()
        except Exception:
            pass
