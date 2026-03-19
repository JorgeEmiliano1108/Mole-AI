import os
from typing import Optional

from ms1_vision.infrastructure.external.redis_diagnosis_publisher import RedisDiagnosisPublisher
from ms1_vision.infrastructure.external.django_patch_client import DjangoPatchClient
from ms1_vision.infrastructure.external.cnn_vision_client import CNNVisionClient
from ms1_vision.infrastructure.database.supabase_diagnostic_repo import SupabaseDiagnosticRepo
from ms1_vision.application.use_cases.create_diagnostic_use_case import CreateDiagnosticUseCase

_redis_publisher: Optional[RedisDiagnosisPublisher] = None
_django_patch_client: Optional[DjangoPatchClient] = None
_vision_client: Optional[CNNVisionClient] = None
_diagnostic_repo: Optional[SupabaseDiagnosticRepo] = None


def get_redis_publisher() -> RedisDiagnosisPublisher:
    global _redis_publisher
    if _redis_publisher is None:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        _redis_publisher = RedisDiagnosisPublisher(redis_url)
    return _redis_publisher


def get_django_patch_client() -> DjangoPatchClient:
    global _django_patch_client
    if _django_patch_client is None:
        base = os.getenv("DJANGO_BASE_URL", "http://django_backend:8000")
        key = os.getenv("HARDWARE_API_KEY", "") #No se debe conectar a la esp32
        _django_patch_client = DjangoPatchClient(base, key)
    return _django_patch_client


def get_vision_client() -> CNNVisionClient:
    global _vision_client
    if _vision_client is None:
        model = os.getenv("CNN_MODEL_PATH", "/app/models/cnn.tflite")
        labels = os.getenv("CNN_LABELS_PATH", "/app/models/labels.json")
        _vision_client = CNNVisionClient(model, labels)
    return _vision_client


def get_diagnostic_repo() -> SupabaseDiagnosticRepo:
    global _diagnostic_repo
    if _diagnostic_repo is None:
        _diagnostic_repo = SupabaseDiagnosticRepo()
    return _diagnostic_repo


def get_diagnostic_use_case() -> CreateDiagnosticUseCase:
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
