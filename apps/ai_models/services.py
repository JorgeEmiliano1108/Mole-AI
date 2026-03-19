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

# Import domain models - usar imports absolutos para ASGI
import sys
from pathlib import Path

# Agregar apps al path para imports absolutos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR / 'apps') not in sys.path:
    sys.path.insert(0, str(BASE_DIR / 'apps'))

try:
    from ai_models.infrastructure.repositories.models import LLMRequest, CNNInference, ModelPerformance
    from core.infrastructure.repositories.models import SensorLog
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
    """
    Helper class to aggregate sensor data for AI requests.
    Reads directly from the Wide-Table sensor_logs.
    """
    
    @staticmethod
    def get_latest_sensor_readings(plant_id: Optional[str] = None,
                                  hours_back: int = 24) -> Dict[str, Any]:
        """
        Get latest sensor reading row for a plant.
        
        Args:
            plant_id: Plant UUID
            hours_back: How many hours back to look
            
        Returns:
            Dictionary with sensor column values
        """
        try:
            cutoff_time = timezone.now() - timedelta(hours=hours_back)
            
            sensor_query = SensorLog.objects.filter(
                recorded_at__gte=cutoff_time
            )
            
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
    """
    HTTP client for Mole-AI microservice
    """
    
    def __init__(self):
        """Initialize client with configuration"""
        self.base_url = getattr(settings, 'MOLE_AI_SERVICE_URL', 'http://localhost:8001')
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
        """
        Make HTTP request to Mole-AI service
        
        Args:
            endpoint: API endpoint (e.g., '/v1/chat/generate')
            method: HTTP method
            data: Request payload
            
        Returns:
            Response data
            
        Raises:
            MoleAIServiceError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        try:
            logger.info(f"Making {method} request to {url}")
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if method.upper() == 'GET':
                    async with session.get(url, headers=headers) as resp:
                        resp.raise_for_status()
                        return await resp.json()
                else:
                    async with session.post(url, headers=headers, json=data) as resp:
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
        """
        Generate chat response using Mole-AI
        
        Args:
            query: User query/question
            context: Optional RAG context passages
            sensor_data: Optional sensor readings
            user_id: Django user ID
            session_id: Session identifier for tracking
            image_base64: Optional base64-encoded image for vision analysis
            **kwargs: Additional parameters (max_tokens, temperature, etc.)
            
        Returns:
            Dictionary containing the AI response and metadata
        """
        start_time = timezone.now()
        llm_request = None
        
        try:
            # Prepare request payload
            payload = {
                'query': query,
                'context': context or [],
                'sensor_data': sensor_data,
                'max_tokens': kwargs.get('max_tokens', 1024),
                'temperature': kwargs.get('temperature', 0.7),
            }
            
            # Include image for vision analysis if provided
            if image_base64:
                payload['image'] = image_base64
            
            # Log the request for tracking (wrapped with sync_to_async for ORM access)
            llm_request = await sync_to_async(LLMRequest.objects.create)(
                user_id=user_id,
                session_id=session_id or f"session_{int(start_time.timestamp())}",
                request_type='chat_conversation',
                prompt=query,
                context={'sensor_data': sensor_data, 'rag_context': context},
                model_name='mole-ai-v3',
                temperature=payload['temperature'],
                max_tokens=payload['max_tokens'],
                status='processing'
            )
            
            # Make async request to Mole-AI service
            response_data = await self._make_request('/api/v1/mole-ai/chat', data=payload)
            
            # Calculate processing time
            processing_time_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            
            # Fix para evitar crash por processing_time_ms nulo
            processing_time_ms = processing_time_ms if processing_time_ms is not None else 0
            
            # Update the request record
            llm_request.response = response_data.get('answer', '')
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
            
            # Update performance metrics (now async)
            await self._update_performance_metrics('mole-ai-v3', processing_time_ms, True)
            
            logger.info(f"Chat response generated in {processing_time_ms}ms")
            
            return {
                'answer': response_data.get('answer'),
                'model_used': response_data.get('model_used'),
                'tokens_generated': response_data.get('tokens_generated'),
                'processing_time_ms': processing_time_ms,
                'request_id': llm_request.id,
                'tactical_alerts_count': response_data.get('answer', '').count('⚠️ ALERTA TÁCTICA')
            }
            
        except Exception as e:
            # Update request with error if we have one
            if 'llm_request' in locals() and llm_request is not None:
                llm_request.status = 'failed'
                llm_request.error_message = str(e)
                llm_request.save()
                
                # Update performance metrics for failure (now async)
                await self._update_performance_metrics('mole-ai-v3', 0, False)
            
            logger.error(f"Error generating chat response: {str(e)}")
            raise MoleAIServiceError(f"Failed to generate chat response: {str(e)}")
    
    async def generate_embeddings(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text embeddings using Mole-AI
        
        Args:
            text: Text to embed
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing embedding vector and metadata
        """
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
        """
        Check Mole-AI service health
        
        Returns:
            Health status information
        """
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
            return {
                'is_healthy': False,
                'error': str(e)
            }
    
    async def _update_performance_metrics(self, model_name: str, response_time_ms: int, 
                                   success: bool):
        """Update model performance metrics (async-safe)"""
        try:
            today = timezone.now().date()
            
            # Get or create performance record for today (wrapped with sync_to_async)
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
                # Update existing record with new metrics
                total_requests = performance.total_requests + 1
                success_count = performance.successful_requests + (1 if success else 0)
                fail_count = performance.failed_requests + (0 if success else 1)
                
                # Update averages
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


# Singleton instance for application-wide use
mole_ai_client = MoleAIClient()
sensor_aggregator = SensorDataAggregator()


async def get_enhanced_ai_response(query: str, 
                           plant_id: Optional[str] = None,
                           user_id: Optional[int] = None,
                           session_id: Optional[str] = None,
                           context: Optional[List[str]] = None,
                           image_base64: Optional[str] = None,
                           **kwargs) -> Dict[str, Any]:
    """
    Convenience function to get enhanced AI response with automatic sensor data
    
    Args:
        query: User query
        plant_id: Plant UUID
        user_id: Django user ID
        session_id: Session ID
        context: RAG context
        image_base64: Optional base64 image for vision analysis
        **kwargs: Additional parameters
        
    Returns:
        Enhanced AI response with sensor data integration
    """
    # Get latest sensor data
    sensor_data = sensor_aggregator.get_latest_sensor_readings(
        plant_id=plant_id,
        hours_back=24
    )
    
    # Generate response (async)
    return await mole_ai_client.generate_chat_response(
        query=query,
        context=context,
        sensor_data=sensor_data,
        user_id=user_id,
        session_id=session_id,
        image_base64=image_base64,
        **kwargs
    )