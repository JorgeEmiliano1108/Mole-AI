"""
Infrastructure Layer - Adapter: Redis Event Publisher
Skill 01: Arquitectura Hexagonal - Implementa EventPublisherPort
Skill 03: Async - usa redis.asyncio
"""
from typing import Optional
import json

# Importamos explícitamente las clases asíncronas para ayudar al linter
from redis.asyncio import Redis, from_url
import structlog

from app.application.ports import EventPublisherPort
from app.domain.entities import DiagnosticResult, DiagnosticEvent
from app.core.config import settings

logger = structlog.get_logger()


class RedisEventPublisher(EventPublisherPort):
    """Implementa EventPublisherPort usando redis.asyncio."""
    
    def __init__(self, redis_url: Optional[str] = None, channel_prefix: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.channel_prefix = channel_prefix or settings.REDIS_CHANNEL_PREFIX
        self._client: Optional[Redis] = None
    
    async def _get_client(self) -> Redis:
        if self._client is None:
            self._client = from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client
    
    async def is_healthy(self) -> bool:
        try:
            client = await self._get_client()
            # Silenciamos el falso positivo del linter sobre la firma síncrona
            await client.ping()  # type: ignore
            return True
        except Exception:
            return False
    
    async def publish_diagnostic_completed(
        self,
        diagnostic: DiagnosticResult,
        diagnostic_id: str,
    ) -> None:
        event = DiagnosticEvent(
            event_type="diagnostic.completed",
            plant_id=diagnostic.plant_id,
            diagnostic_id=diagnostic_id,
            condition=diagnostic.condition,
            severity=diagnostic.severity,
            ph_predicted=diagnostic.ph_predicted,
            timestamp=diagnostic.timestamp.isoformat() if diagnostic.timestamp else "",
        )
        
        channel = f"{self.channel_prefix}diagnostics"
        
        try:
            client = await self._get_client()
            # Silenciamos el falso positivo del linter
            await client.publish(channel, json.dumps(event.to_payload()))  # type: ignore
            logger.info("event_published", channel=channel, diagnostic_id=diagnostic_id)
        except Exception as e:
            logger.error("redis_publish_failed", error=str(e))
            raise
    
    async def publish_diagnostic_failed(
        self,
        plant_id: str,
        error: str,
    ) -> None:
        event = {
            "event_type": "diagnostic.failed",
            "plant_id": plant_id,
            "error": error,
        }
        
        channel = f"{self.channel_prefix}diagnostics"
        
        try:
            client = await self._get_client()
            # Silenciamos el falso positivo del linter
            await client.publish(channel, json.dumps(event))  # type: ignore
            logger.warning("diagnostic_failed", plant_id=plant_id, error=error)
        except Exception as e:
            logger.error("redis_publish_failed", error=str(e))
            raise