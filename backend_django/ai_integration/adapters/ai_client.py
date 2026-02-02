import httpx
import asyncio
from typing import Dict, Any, Optional
import base64
import logging
import random
import time
from functools import wraps

from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True
):
    """
    Decorador para reintentos con backoff exponencial y jitter
    
    Args:
        max_retries: Número máximo de reintentos
        initial_delay: Delay inicial en segundos
        max_delay: Delay máximo en segundos
        backoff_factor: Factor de multiplicación del delay
        jitter: Si se añade variación aleatoria para evitar thundering herd
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
                    last_exception = e
                    
                    # No reintentar en errores de cliente (4xx) excepto 429 (rate limit)
                    if isinstance(e, httpx.HTTPStatusError):
                        if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                            logger.error(f"Error de cliente no reintentable (status {e.response.status_code}): {str(e)}")
                            raise e
                    
                    # Último intento, propagar excepción
                    if attempt == max_retries:
                        logger.error(f"Fallaron todos los {max_retries + 1} intentos. Último error: {str(e)}")
                        raise e
                    
                    # Calcular delay con backoff exponencial
                    delay = min(initial_delay * (backoff_factor ** attempt), max_delay)
                    
                    # Añadir jitter para evitar sincronización de peticiones
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    # Actualizar métricas
                    _retry_metrics["total_retries"] += 1
                    
                    logger.warning(
                        f"Intento {attempt + 1}/{max_retries + 1} fallido: {str(e)}. "
                        f"Reintentando en {delay:.2f} segundos..."
                    )
                    
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    # Para otros tipos de errores, no reintentar
                    logger.error(f"Error no reintentable en {func.__name__}: {str(e)}")
                    raise e
            
            # Este código no debería alcanzarse, pero por si acaso
            if last_exception:
                raise last_exception
            raise Exception("Error inesperado en retry_with_exponential_backoff")
            
        return wrapper
    return decorator

class AIServiceClient:
    """Cliente HTTP para consumir servicios de IA con retry y backoff exponencial"""
    
    def __init__(self):
        self.vision_url = settings.VISION_SERVICE_URL
        self.rag_url = settings.RAG_SERVICE_URL
        self.timeout = settings.EXTERNAL_SERVICE_TIMEOUT
        
        # Configuración de retry
        self.max_retries = getattr(settings, 'AI_CLIENT_MAX_RETRIES', 3)
        self.initial_delay = getattr(settings, 'AI_CLIENT_INITIAL_DELAY', 1.0)
        self.max_delay = getattr(settings, 'AI_CLIENT_MAX_DELAY', 60.0)
        
        self.vision_client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        self.rag_client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    @retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=1.0,
        max_delay=30.0,
        backoff_factor=2.0,
        jitter=True
    )
    async def analyze_plant_image(
        self, 
        image_file, 
        analysis_type: str = "rgb",
        plant_context: str = ""
    ) -> Dict[str, Any]:
        """Envía imagen al servicio de visión y recibe análisis con retry"""
        # Convertir imagen a base64
        image_b64 = self._image_to_base64(image_file)
        
        # Construir payload
        payload = {
            "image_b64": image_b64,
            "analysis_type": analysis_type,
            "plant_context": plant_context
        }
        
        # Llamar al servicio de visión
        response = await self.vision_client.post(
            f"{self.vision_url}/api/v1/analyze",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Análisis de visión completado: {result.get('success', False)}")
        
        return result
    
    @retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0.5,
        max_delay=15.0,
        backoff_factor=2.0,
        jitter=True
    )
    async def detect_plant_type(self, image_file) -> Dict[str, Any]:
        """Detecta tipo de planta usando servicio de visión con retry"""
        image_b64 = self._image_to_base64(image_file)
        
        payload = {"image_b64": image_b64}
        
        response = await self.vision_client.post(
            f"{self.vision_url}/api/v1/detect-plant",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Detección de planta completada: {result.get('success', False)}")
        
        return result
    
    @retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=1.0,
        max_delay=45.0,
        backoff_factor=2.0,
        jitter=True
    )
    async def diagnose_plant(
        self, 
        sensor_data: Dict[str, Any], 
        vision_results: Optional[Dict[str, Any]] = None,
        plant_context: str = ""
    ) -> Dict[str, Any]:
        """Envía datos al servicio RAG para diagnóstico con retry"""
        payload = {
            "sensor_data": sensor_data,
            "vision_results": vision_results,
            "plant_context": plant_context
        }
        
        response = await self.rag_client.post(
            f"{self.rag_url}/api/v1/diagnose",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Diagnóstico RAG completado: {result.get('success', False)}")
        
        return result
    
    @retry_with_exponential_backoff(
        max_retries=5,  # Más reintentos para emergencias
        initial_delay=0.5,
        max_delay=30.0,
        backoff_factor=1.5,  # Más conservador para emergencias
        jitter=True
    )
    async def emergency_diagnosis(
        self, 
        sensor_data: Dict[str, Any], 
        vision_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Diagnóstico de emergencia con retry agresivo"""
        payload = {
            "sensor_data": sensor_data,
            "vision_results": vision_results
        }
        
        response = await self.rag_client.post(
            f"{self.rag_url}/api/v1/emergency-diagnose",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Diagnóstico de emergencia completado: {result.get('success', False)}")
        
        return result
    
    @retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0.5,
        max_delay=10.0,
        backoff_factor=2.0,
        jitter=True
    )
    async def ingest_knowledge_document(
        self, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ingresa documento a la base de conocimiento con retry"""
        payload = {
            "content": content,
            "metadata": metadata
        }
        
        response = await self.rag_client.post(
            f"{self.rag_url}/api/v1/knowledge/ingest",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Documento ingerido: {result.get('success', False)}")
        
        return result
    
    @retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0.3,
        max_delay=5.0,
        backoff_factor=2.0,
        jitter=True
    )
    async def search_knowledge(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Busca en base de conocimiento con retry"""
        params = {"q": query, "limit": limit}
        
        response = await self.rag_client.get(
            f"{self.rag_url}/api/v1/knowledge/search",
            params=params
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Búsqueda completada: {len(result.get('results', []))} resultados")
        
        return result
    
    def _image_to_base64(self, image_file) -> str:
        """Convierte archivo Django a base64"""
        try:
            if hasattr(image_file, 'read'):
                # Es un archivo subido (UploadedFile)
                image_bytes = image_file.read()
                image_file.seek(0)  # Resetear puntero
            else:
                # Es un ContentFile o similar
                image_bytes = image_file.file.read()
                image_file.seek(0)
            
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            return f"data:image/jpeg;base64,{image_b64}"
            
        except Exception as e:
            logger.error(f"Error convirtiendo imagen a base64: {str(e)}")
            raise Exception(f"Error procesando imagen: {str(e)}")
    
    @retry_with_exponential_backoff(
        max_retries=1,
        initial_delay=0.2,
        max_delay=2.0,
        backoff_factor=1.0,
        jitter=False  # Sin jitter para health checks
    )
    async def health_check(self) -> Dict[str, Any]:
        """Verifica salud de los servicios de IA con retry"""
        health_status = {
            "vision_service": False,
            "rag_service": False,
            "overall": False,
            "checked_at": time.time()
        }
        
        try:
            # Verificar servicio de visión
            vision_response = await self.vision_client.get(f"{self.vision_url}/health", timeout=5.0)
            health_status["vision_service"] = vision_response.status_code == 200
        except Exception as e:
            logger.error(f"Servicio de visión no disponible: {str(e)}")
        
        try:
            # Verificar servicio RAG
            rag_response = await self.rag_client.get(f"{self.rag_url}/health", timeout=5.0)
            health_status["rag_service"] = rag_response.status_code == 200
        except Exception as e:
            logger.error(f"Servicio RAG no disponible: {str(e)}")
        
        health_status["overall"] = (
            health_status["vision_service"] and 
            health_status["rag_service"]
        )
        
        return health_status
    
    async def close(self):
        """Cierra clientes HTTP"""
        await self.vision_client.aclose()
        await self.rag_client.aclose()

# Instancia global para ser usada en la aplicación
ai_client = AIServiceClient()

# Métricas globales para monitoreo
_retry_metrics = {
    "total_retries": 0,
    "failed_requests": 0,
    "successful_requests": 0,
    "service_timeouts": 0,
    "connection_errors": 0
}

def get_retry_metrics() -> Dict[str, int]:
    """Obtiene métricas de retry"""
    return _retry_metrics.copy()

def reset_retry_metrics():
    """Resea métricas de retry"""
    for key in _retry_metrics:
        _retry_metrics[key] = 0

# Decorador para manejar errores de IA de manera consistente
def handle_ai_errors(func):
    """Decorador para manejar errores de servicios de IA"""
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            _retry_metrics["successful_requests"] += 1
            return result
        except httpx.TimeoutException:
            _retry_metrics["service_timeouts"] += 1
            _retry_metrics["failed_requests"] += 1
            logger.error(f"Timeout en servicio de IA: {func.__name__}")
            raise
        except httpx.ConnectError:
            _retry_metrics["connection_errors"] += 1
            _retry_metrics["failed_requests"] += 1
            logger.error(f"Error de conexión en servicio de IA: {func.__name__}")
            raise
        except Exception as e:
            _retry_metrics["failed_requests"] += 1
            logger.error(f"Error en servicio de IA: {func.__name__} - {str(e)}")
            raise
    return wrapper