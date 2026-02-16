"""
Services Layer - AI Models Service Integration

This module provides the HTTP client for integrating with the Mole-AI microservice.
Handles sensor data aggregation and AI requests with proper error handling.
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

# Import domain models - usar imports absolutos para ASGI
import sys
import os
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


class MoleAIServiceError(Exception):
    """Custom exception for Mole-AI service errors"""
    pass


class SensorDataAggregator:
    """
    Helper class to aggregate sensor data for AI requests
    """
    
    @staticmethod
    def get_latest_sensor_readings(plant_id: Optional[str] = None, 
                                  device_id: Optional[str] = None,
                                  hours_back: int = 24) -> Dict[str, Any]:
        """
        Get latest sensor readings for a plant or device
        
        Args:
            plant_id: Plant identifier
            device_id: Device identifier  
            hours_back: How many hours back to look for sensor data
            
        Returns:
            Dictionary with aggregated sensor data
        """
        try:
            cutoff_time = timezone.now() - timedelta(hours=hours_back)
            
            # Base query for sensor logs
            sensor_query = SensorLog.objects.filter(
                timestamp__gte=cutoff_time
            )
            
            if plant_id:
                sensor_query = sensor_query.filter(plant_id=plant_id)
            if device_id:
                sensor_query = sensor_query.filter(device_id=device_id)
            
            # Get latest reading for each sensor type
            sensor_data = {}
            latest_readings = {}
            
            # Group by sensor type and get latest
            sensor_types = ['temperature', 'humidity', 'soil_moisture', 'ph', 'light']
            
            for sensor_type in sensor_types:
                latest = sensor_query.filter(
                    sensor_type=sensor_type
                ).order_by('-timestamp').first()
                
                if latest:
                    latest_readings[sensor_type] = {
                        'value': latest.value,
                        'unit': latest.unit,
                        'timestamp': latest.timestamp.isoformat(),
                        'device_id': latest.device_id,
                        'plant_id': latest.plant_id
                    }
            
            # Convert to Mole-AI format
            if 'temperature' in latest_readings:
                sensor_data['temperature'] = latest_readings['temperature']['value']
            
            if 'humidity' in latest_readings:
                sensor_data['humidity'] = latest_readings['humidity']['value']
            
            if 'soil_moisture' in latest_readings:
                sensor_data['soil_humidity'] = latest_readings['soil_moisture']['value']
            
            if 'ph' in latest_readings:
                sensor_data['ph_level'] = latest_readings['ph']['value']
            
            # Extract metadata
            if latest_readings:
                first_reading = list(latest_readings.values())[0]
                sensor_data['device_id'] = first_reading.get('device_id')
                sensor_data['plant_id'] = first_reading.get('plant_id')
                sensor_data['timestamp'] = first_reading.get('timestamp')
            
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
    
    def _make_request(self, endpoint: str, method: str = 'POST', 
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
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        try:
            logger.info(f"Making {method} request to {url}")
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=self.timeout)
            else:
                response = requests.post(url, headers=headers, 
                                       json=data, timeout=self.timeout)
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Request successful: {endpoint}")
            return result
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout connecting to Mole-AI service: {url}"
            logger.error(error_msg)
            raise MoleAIServiceError(error_msg)
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Connection error to Mole-AI service: {url}"
            logger.error(error_msg)
            raise MoleAIServiceError(error_msg)
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error from Mole-AI service: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise MoleAIServiceError(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error calling Mole-AI service: {str(e)}"
            logger.error(error_msg)
            raise MoleAIServiceError(error_msg)
    
    def generate_chat_response(self, query: str, 
                             context: Optional[List[str]] = None,
                             sensor_data: Optional[Dict[str, Any]] = None,
                             user_id: Optional[int] = None,
                             session_id: Optional[str] = None,
                             **kwargs) -> Dict[str, Any]:
        """
        Generate chat response using Mole-AI
        
        Args:
            query: User query/question
            context: Optional RAG context passages
            sensor_data: Optional sensor readings
            user_id: Django user ID
            session_id: Session identifier for tracking
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
            
            # Log the request for tracking
            llm_request = LLMRequest.objects.create(
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
            
            # Make request to Mole-AI service
            response_data = self._make_request('/api/v1/mole-ai/chat', data=payload)
            
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
            llm_request.save()
            
            # Update performance metrics
            self._update_performance_metrics('mole-ai-v3', processing_time_ms, True)
            
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
                
                # Update performance metrics for failure
                self._update_performance_metrics('mole-ai-v3', 0, False)
            
            logger.error(f"Error generating chat response: {str(e)}")
            raise MoleAIServiceError(f"Failed to generate chat response: {str(e)}")
    
    def generate_embeddings(self, text: str, **kwargs) -> Dict[str, Any]:
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
            
            response_data = self._make_request('/api/v1/embeddings', data=payload)
            
            return {
                'vector': response_data.get('vector'),
                'dimension': response_data.get('dimension'),
                'model_used': response_data.get('model_used'),
                'processing_time_ms': response_data.get('processing_time_ms')
            }
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise MoleAIServiceError(f"Failed to generate embeddings: {str(e)}")
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check Mole-AI service health
        
        Returns:
            Health status information
        """
        try:
            response_data = self._make_request('/api/v1/health', method='GET')
            
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
    
    def _update_performance_metrics(self, model_name: str, response_time_ms: int, 
                                   success: bool):
        """Update model performance metrics"""
        try:
            today = timezone.now().date()
            
            # Get or create performance record for today
            performance, created = ModelPerformance.objects.get_or_create(
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
                
                performance.save()
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")


# Singleton instance for application-wide use
mole_ai_client = MoleAIClient()
sensor_aggregator = SensorDataAggregator()


def get_enhanced_ai_response(query: str, 
                           plant_id: Optional[str] = None,
                           device_id: Optional[str] = None,
                           user_id: Optional[int] = None,
                           session_id: Optional[str] = None,
                           context: Optional[List[str]] = None,
                           **kwargs) -> Dict[str, Any]:
    """
    Convenience function to get enhanced AI response with automatic sensor data
    
    Args:
        query: User query
        plant_id: Plant identifier
        device_id: Device identifier  
        user_id: Django user ID
        session_id: Session ID
        context: RAG context
        **kwargs: Additional parameters
        
    Returns:
        Enhanced AI response with sensor data integration
    """
    # Get latest sensor data
    sensor_data = sensor_aggregator.get_latest_sensor_readings(
        plant_id=plant_id,
        device_id=device_id,
        hours_back=24
    )
    
    # Generate response
    return mole_ai_client.generate_chat_response(
        query=query,
        context=context,
        sensor_data=sensor_data,
        user_id=user_id,
        session_id=session_id,
        **kwargs
    )