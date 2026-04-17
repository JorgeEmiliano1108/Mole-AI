import os
import requests
from typing import Optional, Any
from fastapi import Header, HTTPException
import logging

from ms1_vision.infrastructure.external.redis_diagnosis_publisher import RedisDiagnosisPublisher
from ms1_vision.infrastructure.external.django_patch_client import DjangoPatchClient
from ms1_vision.infrastructure.external.cnn_vision_client import CNNVisionClient
from ms1_vision.infrastructure.database.supabase_diagnostic_repo import SupabaseDiagnosticRepo
from ms1_vision.application.use_cases.create_diagnostic_use_case import CreateDiagnosticUseCase
from ms1_vision.infrastructure.external.colorimetric_client import ColorimetricPHClient

logger = logging.getLogger("ms1_vision.dependencies")

# Usamos Any para silenciar al Linter estricto al inyectar Adapters en Ports
_redis_publisher: Any = None
_django_patch_client: Any = None
_vision_client: Any = None
_diagnostic_repo: Any = None
_colorimetric_client: Any = None

def get_auth_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract and validate Authorization header. Returns raw token or raises 401."""
    if not authorization:
        raise HTTPException(status_code=401, detail={
            "type": "https://mole.ai/errors/unauthorized",
            "title": "Unauthorized",
            "status": 401,
            "detail": "missing Authorization header",
        })
    auth = authorization.strip()
    token = auth
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    if not token or token.lower() in ("null", "none", "undefined"):
        logger.warning("Rejected invalid token value: %s", authorization)
        raise HTTPException(status_code=401, detail={
            "type": "https://mole.ai/errors/unauthorized",
            "title": "Unauthorized",
            "status": 401,
            "detail": "missing or invalid token",
        })

    # Ciberseguridad IoT: Validación estricta con RFC 1034 (django-backend)
    django_base = os.getenv("DJANGO_BASE_URL", "http://django-backend:8000").rstrip('/')
    validate_path = os.getenv("DJANGO_VALIDATE_TOKEN_PATH", "/api/v1/auth/validate-token/")
    validate_url = f"{django_base}{validate_path}"

    try:
        resp = requests.post(validate_url, headers={"Authorization": f"Bearer {token}"}, timeout=5.0)
    except requests.RequestException as e:
        logger.exception("Token validation request to Django failed: %s", e)
        raise HTTPException(status_code=503, detail={
            "type": "https://mole.ai/errors/service_unavailable",
            "title": "Service Unavailable",
            "status": 503,
            "detail": "Token validation service unavailable",
        })
        
    content_type = resp.headers.get('Content-Type', '') or resp.headers.get('content-type', '')

    if resp.status_code == 200:
        if 'application/json' in content_type.lower():
            return token
        else:
            logger.error("Token validation returned non-JSON success response. url=%s status=%s content_type=%s", validate_url, resp.status_code, content_type)
            raise HTTPException(status_code=401, detail="Error de validación cruzada interno")

    if resp.status_code in (401, 403):
        logger.warning("Rejected token after validation: status=%s", resp.status_code)
        raise HTTPException(status_code=401, detail={
            "type": "https://mole.ai/errors/unauthorized",
            "title": "Unauthorized",
            "status": 401,
            "detail": "invalid or expired token",
        })

    if resp.status_code == 400:
        logger.error("Token validation returned 400. url=%s", validate_url)
        raise HTTPException(status_code=401, detail="Error de validación cruzada interno")

    if resp.status_code >= 500:
        logger.error("Token validation service error: status=%s", resp.status_code)
        raise HTTPException(status_code=503, detail={
            "type": "https://mole.ai/errors/service_unavailable",
            "title": "Service Unavailable",
            "status": 503,
            "detail": "Token validation service error",
        })

    logger.error("Unexpected response from token validation: status=%s", resp.status_code)
    raise HTTPException(status_code=401, detail="Error de validación cruzada interno")


def get_redis_publisher() -> Any:
    global _redis_publisher
    if _redis_publisher is None:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        _redis_publisher = RedisDiagnosisPublisher(redis_url)
    return _redis_publisher


def get_django_patch_client() -> Any:
    global _django_patch_client
    if _django_patch_client is None:
        base = os.getenv("DJANGO_BASE_URL", "http://django-backend:8000")
        key = os.getenv("HARDWARE_API_KEY", "") 
        _django_patch_client = DjangoPatchClient(base, key)
    return _django_patch_client


def get_vision_client() -> Any:
    global _vision_client
    if _vision_client is None:
        model = os.getenv("CNN_MODEL_PATH", "/app/models/cnn.tflite")
        labels = os.getenv("CNN_LABELS_PATH", "/app/models/labels.json")
        try:
            _vision_client = CNNVisionClient(model, labels)
        except Exception as e:
            logger.exception("Failed to initialize CNNVisionClient: %s", e)
            class _StubVisionClient:
                def analyze(self, image_bytes: bytes):
                    from fastapi import HTTPException
                    raise HTTPException(status_code=503, detail="Vision model unavailable")
            _vision_client = _StubVisionClient()
    return _vision_client


def get_diagnostic_repo() -> Any:
    global _diagnostic_repo
    if _diagnostic_repo is None:
        _diagnostic_repo = SupabaseDiagnosticRepo()
    return _diagnostic_repo


def get_colorimetric_client() -> Any:
    global _colorimetric_client
    if _colorimetric_client is None:
        _colorimetric_client = ColorimetricPHClient()
    return _colorimetric_client


def get_diagnostic_use_case() -> CreateDiagnosticUseCase:
    # La inyección se evalúa como Any, silenciando los errores de Ports
    vision = get_vision_client()
    repo = get_diagnostic_repo()
    redis_pub = get_redis_publisher()
    django_client = get_django_patch_client()
    return CreateDiagnosticUseCase(
        vision_client=vision,
        diagnostic_repo=repo,
        django_patch_client=django_client,
        redis_publisher=redis_pub,
    )