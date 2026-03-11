"""
Base HTTP clients for external microservices.

These clients will be used to communicate with FastAPI microservices
when they are implemented in the future.
"""
import logging
import time
from abc import ABC
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import requests
from django.conf import settings
from django.utils import timezone


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
    """Base class for all microservice clients."""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with default configuration."""
        self.session.timeout = self.config.timeout_seconds
        
        # Set headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': f'Mole-AI-Backend/1.0',
        }
        
        if self.config.api_key:
            headers['Authorization'] = f'Bearer {self.config.api_key}'
        
        self.session.headers.update(headers)
    
    def _handle_response(self, response: requests.Response, start_time: float) -> ServiceResponse:
        """Process HTTP response and create ServiceResponse."""
        response_time_ms = int((timezone.now().timestamp() - start_time) * 1000)
        
        try:
            response.raise_for_status()
            data = response.json() if response.content else None
            return ServiceResponse(
                success=True,
                data=data,
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
        except requests.exceptions.HTTPError as e:
            return ServiceResponse(
                success=False,
                error=f"HTTP {response.status_code}: {str(e)}",
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"Response processing error: {str(e)}",
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
    
    def _make_request_with_retry(self, method: str, *args, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.session.request(method, *args, **kwargs)
                
                # Don't retry on client errors (4xx)
                if 400 <= response.status_code < 500:
                    return response
                
                # Retry on server errors (5xx)
                if response.status_code >= 500:
                    if attempt < self.config.max_retries:
                        logger.warning(
                            f"Service {self.config.name} request failed (attempt {attempt + 1}), "
                            f"retrying in {self.config.retry_delay_seconds}s"
                        )
                        time.sleep(self.config.retry_delay_seconds)
                        continue
                
                return response
                
            except (requests.exceptions.Timeout, 
                   requests.exceptions.ConnectionError) as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    logger.warning(
                        f"Service {self.config.name} connection failed (attempt {attempt + 1}), "
                        f"retrying in {self.config.retry_delay_seconds}s"
                    )
                    time.sleep(self.config.retry_delay_seconds)
                    continue
        
        # All retries failed
        raise last_exception
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> ServiceResponse:
        """Make GET request to microservice."""
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        start_time = timezone.now().timestamp()
        
        try:
            response = self._make_request_with_retry('GET', url, params=params)
            return self._handle_response(response, start_time)
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"Request failed: {str(e)}",
                response_time_ms=int((timezone.now().timestamp() - start_time) * 1000)
            )
    
    def post(self, endpoint: str, data: Optional[Dict] = None, 
             files: Optional[Dict] = None) -> ServiceResponse:
        """Make POST request to microservice."""
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        start_time = timezone.now().timestamp()
        
        try:
            if files:
                # For file uploads, don't set JSON content-type
                headers = self.session.headers.copy()
                if 'Content-Type' in headers:
                    del headers['Content-Type']
                response = self._make_request_with_retry(
                    'POST', url, data=data, files=files, headers=headers
                )
            else:
                response = self._make_request_with_retry('POST', url, json=data)
            
            return self._handle_response(response, start_time)
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"Request failed: {str(e)}",
                response_time_ms=int((timezone.now().timestamp() - start_time) * 1000)
            )
    
    def health_check(self) -> ServiceResponse:
        """Check if microservice is healthy."""
        return self.get("api/v1/health")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


class AIMicroserviceClient(BaseMicroserviceClient):
    """Client for AI-related microservices."""
    
    def analyze_image(self, image_data: bytes, model_type: str = "disease_detection") -> ServiceResponse:
        """Send image to AI microservice for analysis."""
        files = {'image': ('image.jpg', image_data, 'image/jpeg')}
        data = {'model_type': model_type}
        return self.post('api/v1/analyze/image', data=data, files=files)
    
    def generate_recommendations(self, context: Dict[str, Any]) -> ServiceResponse:
        """Generate AI recommendations based on context."""
        return self.post('api/v1/recommendations/generate', data=context)
    
    def chat_with_plant_expert(self, message: str, session_id: str) -> ServiceResponse:
        """Send chat message to plant expert AI."""
        data = {'query': message, 'context': [], 'session_id': session_id}
        return self.post('api/v1/mole-ai/chat', data=data)


class DataProcessingMicroserviceClient(BaseMicroserviceClient):
    """Client for data processing microservices."""
    
    def process_sensor_batch(self, sensor_data: List[Dict[str, Any]]) -> ServiceResponse:
        """Process batch of sensor data."""
        return self.post('process/sensors/batch', data={'sensors': sensor_data})
    
    def generate_analytics_report(self, plant_id: str, 
                                 date_range: Dict[str, str]) -> ServiceResponse:
        """Generate analytics report for a plant."""
        return self.post('analytics/report', data={
            'plant_id': plant_id,
            'date_range': date_range
        })


# Factory for creating clients
class MicroserviceClientFactory:
    """Factory for creating microservice clients."""
    
    @staticmethod
    def create_ai_client() -> AIMicroserviceClient:
        """Create AI microservice client."""
        config = ServiceConfig(
            name="AI Service",
            base_url=getattr(settings, 'AI_MICROSERVICE_URL', 'http://localhost:8001'),
            api_key=getattr(settings, 'AI_MICROSERVICE_API_KEY', None),
            timeout_seconds=60,  # AI operations can be slow
        )
        return AIMicroserviceClient(config)
    
    @staticmethod
    def create_data_processing_client() -> DataProcessingMicroserviceClient:
        """Create data processing microservice client."""
        config = ServiceConfig(
            name="Data Processing Service",
            base_url=getattr(settings, 'DATA_PROCESSING_MICROSERVICE_URL', 'http://localhost:8002'),
            api_key=getattr(settings, 'DATA_PROCESSING_MICROSERVICE_API_KEY', None),
            timeout_seconds=30,
        )
        return DataProcessingMicroserviceClient(config)


# Fallback service for when microservices are not available
class FallbackAIService:
    """Fallback service when AI microservice is not available."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_image(self, image_data: bytes, model_type: str = "disease_detection") -> ServiceResponse:
        """Fallback image analysis."""
        self.logger.warning("Using fallback AI service for image analysis")
        return ServiceResponse(
            success=False,
            error="AI microservice not available. Please configure AI_MICROSERVICE_URL."
        )
    
    def generate_recommendations(self, context: Dict[str, Any]) -> ServiceResponse:
        """Fallback recommendation generation."""
        self.logger.warning("Using fallback AI service for recommendations")
        
        # Basic rule-based recommendations as fallback
        recommendations = []
        
        if context.get('temperature', 0) > 30:
            recommendations.append("Consider increasing ventilation or providing shade")
        
        if context.get('humidity', 50) < 30:
            recommendations.append("Consider increasing humidity through misting")
        
        return ServiceResponse(
            success=True,
            data={'recommendations': recommendations, 'source': 'fallback_rules'}
        )