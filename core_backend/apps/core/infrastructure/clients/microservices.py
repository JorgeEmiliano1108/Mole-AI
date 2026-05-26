# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
#
# AVISO DE PROPIEDAD INTELECTUAL:
# Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
# Queda estrictamente prohibida la copia, modificación, distribución,
# sublicenciamiento o uso comercial de este código, total o parcialmente,
# sin la autorización expresa y por escrito de los titulares del Copyright.
#
# Cualquier uso no autorizado será perseguido conforme a la Ley Federal
# del Derecho de Autor (México) y tratados internacionales aplicables.
# =============================================================================
"""
Async HTTP clients for external microservices.

Sprint 4 — Non-blocking I/O evolution:
  Replaced ``requests.Session`` with ``httpx.AsyncClient`` for fully
  asynchronous communication with FastAPI microservices.
  Retry logic uses ``tenacity`` which natively supports async functions.
"""
import logging
from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from django.conf import settings
from django.utils import timezone
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


@dataclass
class ServiceResponse:
    """Standard response structure for microservice calls."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None


@dataclass
class ServiceConfig:
    """Configuration for external services."""
    name: str
    base_url: str
    api_key: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: float = 1.0


class BaseMicroserviceClient(ABC):
    """Base class for all async microservice clients."""

    def __init__(self, config: ServiceConfig):
        self.config = config
        self._client: httpx.AsyncClient | None = None

    def _build_headers(self) -> Dict[str, str]:
        """Build default headers for outgoing requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mole-AI-Backend/1.0",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazily initialize the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout_seconds),
                headers=self._build_headers(),
            )
        return self._client

    @staticmethod
    def _handle_response(
        response: httpx.Response, start_time: float
    ) -> ServiceResponse:
        """Process HTTP response and create ServiceResponse."""
        response_time_ms = int(
            (timezone.now().timestamp() - start_time) * 1000
        )
        try:
            response.raise_for_status()
            data = response.json() if response.content else None
            return ServiceResponse(
                success=True,
                data=data,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
            )
        except httpx.HTTPStatusError as exc:
            return ServiceResponse(
                success=False,
                error=f"HTTP {response.status_code}: {exc}",
                status_code=response.status_code,
                response_time_ms=response_time_ms,
            )
        except Exception as exc:
            return ServiceResponse(
                success=False,
                error=f"Response processing error: {exc}",
                status_code=response.status_code,
                response_time_ms=response_time_ms,
            )

    @retry(
        retry=retry_if_exception_type(
            (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)
        ),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    async def _make_request_with_retry(
        self, method: str, url: str, **kwargs: Any
    ) -> httpx.Response:
        """Make HTTP request with tenacity exponential-backoff retry (M5)."""
        client = await self._get_client()
        response = await client.request(method, url, **kwargs)
        # Raise on server errors to trigger retry
        if response.status_code >= 500:
            response.raise_for_status()
        return response

    async def get(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> ServiceResponse:
        """Make async GET request to microservice."""
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        start_time = timezone.now().timestamp()
        try:
            response = await self._make_request_with_retry(
                "GET", url, params=params
            )
            return self._handle_response(response, start_time)
        except Exception as exc:
            return ServiceResponse(
                success=False,
                error=f"Request failed: {exc}",
                response_time_ms=int(
                    (timezone.now().timestamp() - start_time) * 1000
                ),
            )

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ) -> ServiceResponse:
        """Make async POST request to microservice."""
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        start_time = timezone.now().timestamp()
        try:
            if files:
                # For file uploads, don't set JSON content-type
                client = await self._get_client()
                response = await self._make_request_with_retry(
                    "POST",
                    url,
                    data=data,
                    files=files,
                    headers={
                        k: v
                        for k, v in self._build_headers().items()
                        if k != "Content-Type"
                    },
                )
            else:
                response = await self._make_request_with_retry(
                    "POST", url, json=data
                )
            return self._handle_response(response, start_time)
        except Exception as exc:
            return ServiceResponse(
                success=False,
                error=f"Request failed: {exc}",
                response_time_ms=int(
                    (timezone.now().timestamp() - start_time) * 1000
                ),
            )

    async def health_check(self) -> ServiceResponse:
        """Check if microservice is healthy."""
        return await self.get("api/v1/health")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


class AIMicroserviceClient(BaseMicroserviceClient):
    """Client for AI-related microservices."""

    async def analyze_image(
        self, image_data: bytes, model_type: str = "disease_detection"
    ) -> ServiceResponse:
        """Send image to AI microservice for analysis."""
        files = {"image": ("image.jpg", image_data, "image/jpeg")}
        data = {"model_type": model_type}
        return await self.post("api/v1/analyze/image", data=data, files=files)

    async def generate_recommendations(
        self, context: Dict[str, Any]
    ) -> ServiceResponse:
        """Generate AI recommendations based on context."""
        return await self.post(
            "api/v1/recommendations/generate", data=context
        )

    async def chat_with_plant_expert(
        self, message: str, session_id: str
    ) -> ServiceResponse:
        """Send chat message to plant expert AI."""
        data = {"query": message, "context": [], "session_id": session_id}
        return await self.post("api/v1/mole-ai/chat", data=data)


class DataProcessingMicroserviceClient(BaseMicroserviceClient):
    """Client for data processing microservices."""

    async def process_sensor_batch(
        self, sensor_data: List[Dict[str, Any]]
    ) -> ServiceResponse:
        """Process batch of sensor data."""
        return await self.post(
            "process/sensors/batch", data={"sensors": sensor_data}
        )

    async def generate_analytics_report(
        self, plant_id: str, date_range: Dict[str, str]
    ) -> ServiceResponse:
        """Generate analytics report for a plant."""
        return await self.post(
            "analytics/report",
            data={"plant_id": plant_id, "date_range": date_range},
        )


# Factory for creating clients
class MicroserviceClientFactory:
    """Factory for creating async microservice clients."""

    @staticmethod
    def create_ai_client() -> AIMicroserviceClient:
        """Create AI microservice client."""
        config = ServiceConfig(
            name="AI Service",
            base_url=getattr(
                settings, "AI_MICROSERVICE_URL", "http://localhost:8001"
            ),
            api_key=getattr(settings, "AI_MICROSERVICE_API_KEY", None),
            timeout_seconds=60,  # AI operations can be slow
        )
        return AIMicroserviceClient(config)

    @staticmethod
    def create_data_processing_client() -> DataProcessingMicroserviceClient:
        """Create data processing microservice client (Mole-AI Chat)."""
        # Sincronizamos con la variable de entorno real de tu .env
        config = ServiceConfig(
            name="Mole-AI Service",
            base_url=getattr(
                settings, "MOLE_AI_SERVICE_URL", "http://ms2_chat:8002"
            ),
            api_key=getattr(settings, "MOLE_AI_API_KEY", None),
            timeout_seconds=getattr(settings, "MOLE_AI_TIMEOUT", 120),
        )
        return DataProcessingMicroserviceClient(config)


# Fallback service for when microservices are not available
class FallbackAIService:
    """Fallback service when AI microservice is not available."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def analyze_image(
        self, image_data: bytes, model_type: str = "disease_detection"
    ) -> ServiceResponse:
        """Fallback image analysis."""
        self.logger.warning(
            "Using fallback AI service for image analysis"
        )
        return ServiceResponse(
            success=False,
            error="AI microservice not available. Please configure AI_MICROSERVICE_URL.",
        )

    async def generate_recommendations(
        self, context: Dict[str, Any]
    ) -> ServiceResponse:
        """Fallback recommendation generation."""
        self.logger.warning(
            "Using fallback AI service for recommendations"
        )

        # Basic rule-based recommendations as fallback
        recommendations = []

        if context.get("temperature", 0) > 30:
            recommendations.append(
                "Consider increasing ventilation or providing shade"
            )

        if context.get("humidity", 50) < 30:
            recommendations.append(
                "Consider increasing humidity through misting"
            )

        return ServiceResponse(
            success=True,
            data={
                "recommendations": recommendations,
                "source": "fallback_rules",
            },
        )