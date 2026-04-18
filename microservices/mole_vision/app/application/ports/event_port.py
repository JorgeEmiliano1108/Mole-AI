"""
Puerto de Publicación de Eventos - Skill 01: Interfaz abstracta para pub/sub.
Skill 03: Debe ser async para integrarse con redis.asyncio.
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities import DiagnosticResult, DiagnosticEvent


class EventPublisherPort(ABC):
    """
    Puerto abstracto para publicación de eventos.
    
    Contract: El caso de uso publica eventos sin conocer el broker.
    Implementaciones: Redis Pub/Sub, RabbitMQ, Kafka, etc.
    """
    
    @abstractmethod
    async def publish_diagnostic_completed(self, diagnostic: "DiagnosticResult", diagnostic_id: str) -> None:
        """
        Publica evento de diagnóstico completado.
        
        Args:
            diagnostic: Entidad de dominio con el resultado.
            diagnostic_id: ID único del diagnóstico para trazabilidad.
        """
        pass
    
    @abstractmethod
    async def publish_diagnostic_failed(self, plant_id: str, error: str) -> None:
        """
        Publica evento de diagnóstico fallido.
        
        Args:
            plant_id: ID de la planta que falló.
            error: Descripción del error (no exponer PII).
        """
        pass
    
    @abstractmethod
    async def is_healthy(self) -> bool:
        """Verifica la conexión con el broker de eventos."""
        pass