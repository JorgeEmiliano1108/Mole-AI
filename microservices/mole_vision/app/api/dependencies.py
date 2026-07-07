"""
API Layer - Dependency Injection for FastAPI
Skill 01: Arquitectura Hexagonal - Capa de Adaptadores de Entrada
Skill 02: LFPDPPP - Sanitización EXIF
Skill 03: FastAPI Async - run_in_threadpool para tareas CPU-bound
"""
from io import BytesIO
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, UploadFile, File
from PIL import Image
import structlog
from starlette.concurrency import run_in_threadpool
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import jwt

from app.application.ports import (
    VisionClientPort,
    EventPublisherPort,
    DiagnosticRepositoryPort,
)
from app.infrastructure.adapters.nvidia_vision_adapter import NvidiaVisionAdapter
from app.infrastructure.adapters.redis_publisher import RedisEventPublisher
from app.infrastructure.adapters.supabase_adapter import SupabaseDiagnosticRepository

logger = structlog.get_logger()
security = HTTPBearer()

def clean_exif(image_bytes: bytes) -> bytes:
    """
    Limpia metadatos EXIF/GPS de la imagen usando métodos nativos de Pillow.
    
    IMPORTANTE: Esta función es síncrona porque:
    - Las operaciones de lectura de metadatos son rápidas
    - FastAPI la envía automáticamente al ThreadPool cuando se llama con run_in_threadpool
    """
    img = Image.open(BytesIO(image_bytes))
    
    exif = img.getexif()
    if exif:
        exif.clear()
    
    buffer = BytesIO()
    img.save(buffer, format=img.format or "JPEG")
    return buffer.getvalue()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """Extrae y valida el JWT usando la clave local.
    Se espera que el token sea firmado con HS256 y la clave definida en JWT_SECRET_KEY.
    """
    token = credentials.credentials
    try:
        # Mantenemos TODAS las validaciones críticas.
        claims = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": True, "verify_exp": True},
            leeway=30,
        )
    except jwt.ExpiredSignatureError as exc:
        logger.error("jwt_validation_failed", error_type="ExpiredSignatureError", detail=str(exc))
        raise HTTPException(status_code=401, detail="Token expirado. Por favor inicie sesión nuevamente.")
    except jwt.InvalidSignatureError as exc:
        logger.error("jwt_validation_failed", error_type="InvalidSignatureError", detail=str(exc))
        raise HTTPException(status_code=401, detail="Firma inválida. Las claves JWT_SECRET_KEY no coinciden.")
    except jwt.PyJWTError as exc:
        logger.error("jwt_validation_failed", error_type=type(exc).__name__, detail=str(exc))
        raise HTTPException(status_code=401, detail=f"Error criptográfico: {type(exc).__name__}")
    except Exception as exc:
        logger.error("jwt_validation_failed", error_type=type(exc).__name__, detail=str(exc))
        raise HTTPException(status_code=401, detail="Token inválido.")
    return claims


_vision_adapter: Optional[VisionClientPort] = None
_event_publisher: Optional[EventPublisherPort] = None
_diagnostic_repository: Optional[DiagnosticRepositoryPort] = None


def get_vision_client() -> VisionClientPort:
    """Factory for vision client — NVIDIA NIM only (Mock via test fakes)."""
    global _vision_adapter
    if _vision_adapter is not None:
        return _vision_adapter

    # 1) Try NVIDIA NIM
    try:
        adapter = NvidiaVisionAdapter()
        if adapter.is_ready():
            _vision_adapter = adapter
            logger.info("vision_client_factory", chosen="nvidia_nim")
            return _vision_adapter
    except Exception as exc:
        logger.warning("nvidia_init_failed", error=str(exc))

    # 2) No fallback — NVIDIA NIM is the only production adapter
    raise RuntimeError(
        "NVIDIA NIM vision adapter not available. "
        "Use MockVisionAdapter from tests/fakes/ for CI/testing."
    )


def get_event_publisher() -> EventPublisherPort:
    """Factory para el publicador de eventos (Redis)."""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = RedisEventPublisher()
    return _event_publisher


def get_diagnostic_repository() -> DiagnosticRepositoryPort:
    """Factory para el repositorio de diagnósticos (Supabase)."""
    global _diagnostic_repository
    if _diagnostic_repository is None:
        _diagnostic_repository = SupabaseDiagnosticRepository()
    return _diagnostic_repository


AuthenticatedUser = Annotated[dict, Depends(get_current_user)]
VisionClient = Annotated[VisionClientPort, Depends(get_vision_client)]
EventPublisher = Annotated[EventPublisherPort, Depends(get_event_publisher)]
DiagnosticRepository = Annotated[DiagnosticRepositoryPort, Depends(get_diagnostic_repository)]


async def get_image_file(
    image: UploadFile = File(...),
) -> bytes:
    """Lee y sanitiza la imagen subida por el usuario."""
    contents = await image.read()
    
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail={"type": "https://mole.ai/errors/bad_request", "title": "Image Too Large", "status": 400},
        )
    
    try:
        cleaned_contents = await run_in_threadpool(clean_exif, contents)
    except Exception as e:
        logger.error("exif_cleaning_failed", error=str(e))
        raise HTTPException(
            status_code=400,
            detail={"type": "https://mole.ai/errors/bad_request", "title": "Invalid Image", "status": 400},
        )
    
    return cleaned_contents