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
from app.domain.schemas import DiagnosticResponseSchema, PhStripResponseSchema, HealthCheckSchema, ConditionCategorySchema, SeverityLevelSchema 
from app.domain.entities import DiagnosticResult

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
@router.post("/analyze/", response_model=DiagnosticResponseSchema)
@limiter.limit("5/minute")
async def analyze_vision(
    request: Request,
    user: AuthenticatedUser,
    image_bytes: bytes = Depends(get_image_file),
    use_case: AnalyzePlantUseCase = Depends(get_analyze_use_case),
) -> DiagnosticResponseSchema:
    """Endpoint para analizar una imagen de planta."""
    try:
        plant_id = user.get("plant_id", "unknown")
        
        diagnostic = await use_case.execute(
            image_bytes=image_bytes,
            plant_id=plant_id,
            user_claims=user,
        )
        
        return DiagnosticResponseSchema(
            id="",
            plant_id=diagnostic.plant_id,
            species=diagnostic.species,
            condition=diagnostic.condition,
            condition_category=ConditionCategorySchema(diagnostic.condition_category.value),
            severity=SeverityLevelSchema(diagnostic.severity.value),
            confidence=diagnostic.confidence,
            ph_predicted=diagnostic.ph_predicted,
            # ✅ Fallback seguro por si timestamp es None (evita el error de Pylance)
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


@router.post("/analyze-ph-strip/", response_model=PhStripResponseSchema)
async def analyze_ph_strip(
    user: AuthenticatedUser, 
    image_bytes: bytes = Depends(get_image_file),
) -> PhStripResponseSchema:
    """Endpoint para analizar tira reactiva de pH."""
    from app.infrastructure.adapters.colorimetric_adapter import ColorimetricAdapter
    
    try:
        adapter = ColorimetricAdapter()
        ph_value = adapter.estimate_ph(image_bytes)
        
        return PhStripResponseSchema(
            estimated_ph=ph_value,
            method="Colorimetry_Euclidean_RGB",
        )
    except Exception as exc:
        logger.error("ph_strip_failed", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail={"type": "https://mole.ai/errors/internal", "title": "pH Analysis Failed"},
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