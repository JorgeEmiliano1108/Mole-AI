"""
API Layer - Routers
Arquitectura Hexagonal - Capa de Adaptadores de Entrada
"""
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
import structlog

from app.api.limiter import limiter
from app.api.dependencies import (
    get_current_user,
    get_image_file,
    get_vision_client,
    get_event_publisher,
    get_diagnostic_repository,
    AuthenticatedUser,
)
from app.application.use_cases.analyze_plant import AnalyzePlantUseCase
from app.domain.schemas import (
    DiagnosticResponseV2Schema, HealthCheckSchema,
    PlantDiagnosisSchema, GrowthStageSchema,
    AfflictionTypeSchema, ProgressionStageSchema,
    SeverityLevelSchema,
)
from app.domain.entities import PlantDiagnosis
from app.core.nom059 import check_nom059_violation

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/vision")


def get_analyze_use_case(
    vision=Depends(get_vision_client),
    events=Depends(get_event_publisher),
    repo=Depends(get_diagnostic_repository),
) -> AnalyzePlantUseCase:
    return AnalyzePlantUseCase(
        vision_client=vision,
        event_publisher=events,
        diagnostic_repository=repo,
    )


# Vision Analysis — 5 requests/minute per client IP (guards NVIDIA token budget)
@router.post("/analyze/", response_model=DiagnosticResponseV2Schema)
@limiter.limit("5/minute")
async def analyze_vision(
    request: Request,
    user: AuthenticatedUser,
    image_bytes: bytes = Depends(get_image_file),
    use_case: AnalyzePlantUseCase = Depends(get_analyze_use_case),
) -> DiagnosticResponseV2Schema:
    """Endpoint para analizar una imagen de planta."""
    try:
        plant_id = user.get("plant_id", "unknown")
        
        diagnostic = await use_case.execute(
            image_bytes=image_bytes,
            plant_id=plant_id,
            user_claims=user,
        )

        # NOM-059-SEMARNAT compliance: block protected species responses
        if check_nom059_violation(diagnostic):
            logger.warning(
                "nom059_violation_blocked",
                plant_id=diagnostic.plant_id,
                species_common=diagnostic.species_common,
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "type": "https://mole.ai/errors/nom059",
                    "title": "Solicitud prohibida",
                    "status": 403,
                    "detail": (
                        "Esta consulta involucra una especie protegida por la "
                        "NOM-059-SEMARNAT. Para información oficial, consulte "
                        "la lista SEMARNAT."
                    ),
                },
            )

        return DiagnosticResponseV2Schema(
            id="",
            plant_id=diagnostic.plant_id,
            diagnosis=PlantDiagnosisSchema(
                species_common=diagnostic.species_common,
                species_scientific=diagnostic.species_scientific,
                growth_stage=GrowthStageSchema(diagnostic.growth_stage.value),
                affliction_name=diagnostic.affliction_name,
                affliction_type=AfflictionTypeSchema(diagnostic.affliction_type.value),
                causal_agent=diagnostic.causal_agent,
                severity=SeverityLevelSchema(diagnostic.severity.value),
                progression=ProgressionStageSchema(diagnostic.progression.value),
                confidence=diagnostic.confidence,
                immediate_actions=diagnostic.immediate_actions,
                preventive_measures=diagnostic.preventive_measures,
                mitigation_steps=diagnostic.mitigation_steps,
                ph_predicted=diagnostic.ph_predicted,
                model_version=diagnostic.model_version,
            ),
            timestamp=diagnostic.timestamp or datetime.now(timezone.utc).replace(tzinfo=None),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("diagnostic_failed", error=str(exc), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "type": "https://mole.ai/errors/internal",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "Diagnostic processing failed",
            },
        )

@router.get("/health/", response_model=HealthCheckSchema)
async def health() -> HealthCheckSchema:
    """Health check básico."""
    return HealthCheckSchema(status="ok")


@router.get("/healthz/")
async def healthz() -> dict:
    """Health check completo con verificación de componentes."""
    from app.infrastructure.adapters.nvidia_vision_adapter import NvidiaVisionAdapter
    from app.infrastructure.adapters.redis_publisher import RedisEventPublisher

    health = {
        "model_loaded": False,
        "redis_ok": False,
    }

    try:
        adapter = NvidiaVisionAdapter()
        health["model_loaded"] = adapter.is_ready()
    except Exception:
        health["model_loaded"] = False
    
    try:
        publisher = RedisEventPublisher()
        health["redis_ok"] = await publisher.is_healthy()
    except Exception:
        health["redis_ok"] = False
    
    if all(health.values()):
        return {"status": "ok", "checks": health}
    raise HTTPException(status_code=503, detail={"status": "unhealthy", "checks": health})