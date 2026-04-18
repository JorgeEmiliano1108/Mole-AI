"""
Application Layer - Caso de Uso: Analyze Plant
Skill 01: Arquitectura Hexagonal - Capa de Application
Skill 02: LFPDPPP - Sin PII en logs
Skill 03: Async - await en publicación de eventos
"""
from typing import Optional
from dataclasses import replace
import structlog

from app.domain.entities import DiagnosticResult
from app.application.ports import (
    VisionClientPort,
    EventPublisherPort,
    DiagnosticRepositoryPort,
)

logger = structlog.get_logger()


class AnalyzePlantUseCase:
    """
    Caso de uso para analizar una imagen de planta.
    
    Inyección de dependencias en el constructor (DDD).
    """
    
    def __init__(
        self,
        vision_client: VisionClientPort,
        event_publisher: EventPublisherPort,
        diagnostic_repository: DiagnosticRepositoryPort,
    ):
        self.vision_client = vision_client
        self.event_publisher = event_publisher
        self.diagnostic_repository = diagnostic_repository
    
    async def execute(
        self,
        image_bytes: bytes,
        plant_id: str,
        user_claims: Optional[dict] = None,
    ) -> DiagnosticResult:
        """
        Ejecuta el análisis de la planta.
        
        Args:
            image_bytes: Bytes de la imagen (ya limpia de EXIF)
            plant_id: ID de la planta a analizar
            user_claims: Claims del JWT autenticado
            
        Returns:
            DiagnosticResult: Entidad de dominio con el resultado
        """
        if not self.vision_client.is_ready():
            logger.error("vision_model_not_ready")
            raise RuntimeError("Vision model not available")
        
        diagnostic = await self.vision_client.analyze(image_bytes)
        diagnostic = replace(diagnostic, plant_id=plant_id)
        
        diagnostic_id = await self.diagnostic_repository.save_diagnostic(diagnostic)
        
        try:
            await self.event_publisher.publish_diagnostic_completed(
                diagnostic=diagnostic,
                diagnostic_id=diagnostic_id,
            )
        except Exception as e:
            logger.warning(
                "event_publish_failed",
                diagnostic_id=diagnostic_id,
                error=str(e),
            )
        
        logger.info(
            "diagnostic_completed",
            diagnostic_id=diagnostic_id,
            plant_id=plant_id,
            condition=diagnostic.condition,
            severity=diagnostic.severity.value,
        )
        
        return diagnostic