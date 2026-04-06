import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from ms1_vision.app.dependencies import get_diagnostic_use_case, get_auth_token, get_colorimetric_client
from ms1_vision.application.use_cases.create_diagnostic_use_case import CreateDiagnosticUseCase
from ms1_vision.domain.schemas import DiagnosticModel
from ms1_vision.infrastructure.external.colorimetric_client import ColorimetricPHClient

# Inicializar logger para cumplimiento de trazabilidad
logger = logging.getLogger("ms1_vision.routes")

router = APIRouter(prefix="/api/v1/vision")

# Esquema de salida para la colorimetría (Ética de la IA - Disclaimer obligatorio)
class ColorimetricPHResponse(BaseModel):
    estimated_ph: float
    method: str = "Colorimetry_Euclidean_RGB"
    disclaimer: str = "Valor estimado por visión algorítmica. No sustituye un análisis químico de laboratorio."


@router.post("/analyze", response_model=DiagnosticModel)
async def analyze_vision(
    file: UploadFile = File(...),
    use_case: CreateDiagnosticUseCase = Depends(get_diagnostic_use_case),
    token: str = Depends(get_auth_token),
) -> DiagnosticModel:
    image_bytes = await file.read()
    try:
        result = await use_case.execute(image_bytes=image_bytes, plant_id="unknown", token=token)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Fallo critico en la inferencia o persistencia de la IA: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail={
            "type": "https://mole.ai/errors/internal",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "an internal error occurred",
        })


@router.post("/analyze-ph-strip", response_model=ColorimetricPHResponse)
async def analyze_ph_strip(
    file: UploadFile = File(...),
    color_client: ColorimetricPHClient = Depends(get_colorimetric_client),
    token: str = Depends(get_auth_token),
) -> ColorimetricPHResponse:
    image_bytes = await file.read()
    try:
        ph_val = color_client.estimate_ph_from_strip(image_bytes)
        return ColorimetricPHResponse(estimated_ph=ph_val)
    except Exception as exc:
        logger.error("Error procesando tira reactiva: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail={
            "type": "https://mole.ai/errors/internal",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "Error interno analizando el pH de la tira reactiva.",
        })


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/healthz")
async def healthz() -> dict:
    from ms1_vision.app.dependencies import get_vision_client, get_django_patch_client, get_redis_publisher
    import httpx
    import asyncio
    from fastapi import HTTPException

    health = {
        "model_loaded": False,
        "django_ok": False,
        "redis_ok": False,
    }

    try:
        vc = get_vision_client()
        if getattr(vc, "interpreter", None) is not None:
            health["model_loaded"] = True
    except Exception:
        health["model_loaded"] = False

    try:
        dp = get_django_patch_client()
        url = dp.base_url.rstrip("/") + "/health"
        async def _check_django():
            async with httpx.AsyncClient(timeout=1.0) as client:
                r = await client.get(url)
                return r.status_code == 200
        try:
            health["django_ok"] = asyncio.get_event_loop().run_until_complete(_check_django())
        except Exception:
            health["django_ok"] = False
    except Exception:
        health["django_ok"] = False

    try:
        rp = get_redis_publisher()
        redis_client = getattr(rp, "_redis", None)
        if redis_client is not None:
            try:
                health["redis_ok"] = bool(asyncio.get_event_loop().run_until_complete(redis_client.ping()))
            except Exception:
                health["redis_ok"] = False
    except Exception:
        health["redis_ok"] = False

    if all(health.values()):
        return {
            "status": "ok",
            "checks": health,
        }
    raise HTTPException(status_code=503, detail={"status": "unhealthy", "checks": health})