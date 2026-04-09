# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Services Layer - AI Models Service Integration

This module provides the HTTP client for integrating with the Mole-AI microservice.
Handles sensor data aggregation and AI requests with proper error handling.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import timedelta

import asyncio
import aiohttp
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import sys
from pathlib import Path

# Agregar apps al path para imports absolutos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR / 'apps') not in sys.path:
    sys.path.insert(0, str(BASE_DIR / 'apps'))

try:
    from apps.ai_models.models import LLMRequest, CNNInference, ModelPerformance
    from apps.core.models import SensorLog
except ImportError as e:
    print(f"⚠️ Error importando modelos: {e}")
    LLMRequest = None
    CNNInference = None
    ModelPerformance = None
    SensorLog = None

logger = logging.getLogger(__name__)

# Sensor columns in the Wide Table (sensor_logs).
SENSOR_COLUMNS: list = [
    'soil_humidity', 'air_temperature', 'uv_index', 'light_level', 'ph_level',
]

class MoleAIServiceError(Exception):
    """Custom exception for Mole-AI service errors"""

class SensorDataAggregator:
    """Helper class to aggregate sensor data for AI requests."""
    
    @staticmethod
    def get_latest_sensor_readings(plant_id: Optional[str] = None,
                                  hours_back: int = 24) -> Dict[str, Any]:
        # FIX: Validación defensiva para satisfacer al linter y evitar crashes
        if SensorLog is None:
            logger.warning("Modelo SensorLog no disponible. Saltando agregación de sensores.")
            return {}

        try:
            cutoff_time = timezone.now() - timedelta(hours=hours_back)
            
            sensor_query = SensorLog.objects.filter(recorded_at__gte=cutoff_time)
            
            if plant_id:
                sensor_query = sensor_query.filter(plant_id=plant_id)
            
            latest = sensor_query.order_by('-recorded_at').first()
            
            if not latest:
                logger.info("No sensor readings found in time window")
                return {}
            
            sensor_data: Dict[str, Any] = {
                'plant_id': str(latest.plant_id),
                'recorded_at': latest.recorded_at.isoformat() if latest.recorded_at else None,
            }
            for col in SENSOR_COLUMNS:
                val = getattr(latest, col, None)
                if val is not None:
                    sensor_data[col] = val
            
            logger.info(f"Aggregated sensor data: {len(sensor_data)} fields")
            return sensor_data
            
        except Exception as e:
            logger.error(f"Error aggregating sensor data: {str(e)}")
            return {}

class MoleAIClient:
    """HTTP client for Mole-AI microservice"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'MOLE_AI_SERVICE_URL', 'http://ms2_chat:8002')
        self.timeout = getattr(settings, 'MOLE_AI_TIMEOUT', 120)
        self.api_key = getattr(settings, 'MOLE_AI_API_KEY', None)
        
        logger.info(f"Mole-AI client initialized with URL: {self.base_url}")
    
    @retry(
        retry=retry_if_exception_type((asyncio.TimeoutError, aiohttp.ClientConnectionError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _make_request(self, endpoint: str, method: str = 'POST', 
                            data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        try:
            logger.info(f"Making {method} request to {url}")
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if method.upper() == 'GET':
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 422:
                            error_detail = await resp.text()
                            logger.error(f"422 Validation Error Details (GET): {error_detail}")
                        resp.raise_for_status()
                        return await resp.json()
                else:
                    async with session.post(url, headers=headers, json=data) as resp:
                        if resp.status == 422:
                            error_detail = await resp.text()
                            logger.error(f"422 Validation Error Details (POST): {error_detail}")
                        resp.raise_for_status()
                        return await resp.json()

        except asyncio.TimeoutError:
            error_msg = f"Timeout connecting to Mole-AI service: {url}"
            logger.error(error_msg)
            raise MoleAIServiceError(error_msg)
        except aiohttp.ClientConnectionError:
            error_msg = f"Connection error to Mole-AI service: {url}"
            logger.error(error_msg)
            raise MoleAIServiceError(error_msg)
        except aiohttp.ClientResponseError as e:
            error_msg = f"HTTP error from Mole-AI service: {e.status} - {getattr(e, 'message', repr(e))}"
            logger.error(error_msg)
            raise MoleAIServiceError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error calling Mole-AI service: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MoleAIServiceError(error_msg)
    
    async def generate_chat_response(self, query: str, 
                             context: Optional[List[str]] = None,
                             sensor_data: Optional[Dict[str, Any]] = None,
                             user_id: Optional[int] = None,
                             session_id: Optional[str] = None,
                             image_base64: Optional[str] = None,
                             **kwargs) -> Dict[str, Any]:
        start_time = timezone.now()
        llm_request = None
        
        try:
            payload = {
                'message': query,
                'user_id': str(user_id) if user_id else "anon",
                'context': context or [],
                'sensor_data': sensor_data,
                'max_tokens': kwargs.get('max_tokens', 1024),
                'temperature': kwargs.get('temperature', 0.7),
            }
            
            if image_base64:
                payload['image'] = image_base64
            
            if LLMRequest is not None:
                llm_request = await sync_to_async(LLMRequest.objects.create)(
                    user_id=user_id,
                    session_id=session_id or f"session_{int(start_time.timestamp())}",
                    request_type='chat_conversation',
                    prompt=query,
                    context={'sensor_data': sensor_data, 'rag_context': context},
                    model_name='qwen2.5:7b',
                    temperature=payload['temperature'],
                    max_tokens=payload['max_tokens'],
                    status='processing'
                )
            
            response_data = await self._make_request('/api/v1/mole-ai/chat', data=payload)
            
            processing_time_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            processing_time_ms = processing_time_ms if processing_time_ms is not None else 0
            
            # FIX: Traducción estricta de la llave 'respuesta' de MS2 a la variable que usa Django
            respuesta_texto = response_data.get('respuesta', '')
            
            # FIX: Forzar que el disclaimer sea una cadena de texto, nunca un booleano
            disclaimer_raw = response_data.get('disclaimer')
            if isinstance(disclaimer_raw, bool) or str(disclaimer_raw).lower() == 'true':
                disclaimer_texto = "AVISO LEGAL: Información generada por IA. Consulte a un ingeniero agrónomo."
            else:
                disclaimer_texto = str(disclaimer_raw) if disclaimer_raw else ""

            if llm_request is not None:
                llm_request.response = respuesta_texto
                llm_request.response_metadata = {
                    'model_used': response_data.get('model_used'),
                    'tokens_generated': response_data.get('tokens_generated'),
                    'processing_time_ms': response_data.get('processing_time_ms'),
                    'sensor_data_used': bool(sensor_data),
                    'context_used': len(context or []),
                }
                llm_request.token_usage = {
                    'generated': response_data.get('tokens_generated', 0),
                    'processing_time_ms': processing_time_ms
                }
                llm_request.processing_time_ms = processing_time_ms
                llm_request.status = 'completed'
                llm_request.completed_at = timezone.now()
                await sync_to_async(llm_request.save)()
            
            await self._update_performance_metrics('qwen2.5:7b', processing_time_ms, True)
            
            logger.info(f"Chat response generated in {processing_time_ms}ms")
            
            # FIX: Empaquetamos la respuesta de vuelta al frontend usando las llaves en inglés que tu JS espera ('answer')
            return {
                'answer': respuesta_texto, 
                'model_used': response_data.get('model_used'),
                'tokens_generated': response_data.get('tokens_generated'),
                'processing_time_ms': processing_time_ms,
                'request_id': llm_request.id if llm_request else None,
                'tactical_alerts_count': str(respuesta_texto).count('⚠️ ALERTA TÁCTICA'),
                'disclaimer': disclaimer_texto,
            }
            
        except Exception as e:
            if 'llm_request' in locals() and llm_request is not None:
                llm_request.status = 'failed'
                llm_request.error_message = str(e)
                await sync_to_async(llm_request.save)()
                
            await self._update_performance_metrics('mole-ai-v3', 0, False)
            logger.error(f"Error generating chat response: {str(e)}")
            raise MoleAIServiceError(f"Failed to generate chat response: {str(e)}")
    
    async def generate_embeddings(self, text: str, **kwargs) -> Dict[str, Any]:
        try:
            payload = {
                'text': text,
                'model': kwargs.get('model', 'sentence-transformers/all-mpnet-base-v2')
            }
            response_data = await self._make_request('/api/v1/embeddings', data=payload)
            return {
                'vector': response_data.get('vector'),
                'dimension': response_data.get('dimension'),
                'model_used': response_data.get('model_used'),
                'processing_time_ms': response_data.get('processing_time_ms')
            }
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise MoleAIServiceError(f"Failed to generate embeddings: {str(e)}")
    
    async def check_health(self) -> Dict[str, Any]:
        try:
            response_data = await self._make_request('/api/v1/health', method='GET')
            return {
                'is_healthy': response_data.get('is_healthy'),
                'uptime_seconds': response_data.get('uptime_seconds'),
                'version': response_data.get('version'),
                'models': response_data.get('models', [])
            }
        except Exception as e:
            logger.error(f"Error checking health: {str(e)}")
            return {'is_healthy': False, 'error': str(e)}
    
    async def _update_performance_metrics(self, model_name: str, response_time_ms: int, success: bool):
        if ModelPerformance is None:
            return
        try:
            today = timezone.now().date()
            performance, created = await sync_to_async(ModelPerformance.objects.get_or_create)(
                model_name=model_name,
                model_version='1.0.0',
                metrics_date=today,
                metrics_hour=timezone.now().hour,
                defaults={
                    'model_category': 'llm',
                    'avg_response_time_ms': response_time_ms,
                    'p95_response_time_ms': response_time_ms,
                    'p99_response_time_ms': response_time_ms,
                    'avg_memory_usage_mb': 0.0,
                    'peak_memory_usage_mb': 0.0,
                    'cpu_usage_percent': 0.0,
                    'total_requests': 1,
                    'successful_requests': 1 if success else 0,
                    'failed_requests': 0 if success else 1,
                }
            )
            
            if not created:
                total_requests = performance.total_requests + 1
                success_count = performance.successful_requests + (1 if success else 0)
                fail_count = performance.failed_requests + (0 if success else 1)
                
                performance.avg_response_time_ms = (
                    (performance.avg_response_time_ms * performance.total_requests + response_time_ms) / 
                    total_requests
                )
                performance.total_requests = total_requests
                performance.successful_requests = success_count
                performance.failed_requests = fail_count
                
                await sync_to_async(performance.save)()
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")

mole_ai_client = MoleAIClient()
sensor_aggregator = SensorDataAggregator()

async def get_enhanced_ai_response(query: str, 
                           plant_id: Optional[str] = None,
                           user_id: Optional[int] = None,
                           session_id: Optional[str] = None,
                           context: Optional[List[str]] = None,
                           image_base64: Optional[str] = None,
                           **kwargs) -> Dict[str, Any]:
    sensor_data = sensor_aggregator.get_latest_sensor_readings(plant_id=plant_id, hours_back=24)
    return await mole_ai_client.generate_chat_response(
        query=query, context=context, sensor_data=sensor_data,
        user_id=user_id, session_id=session_id, image_base64=image_base64, **kwargs
    )