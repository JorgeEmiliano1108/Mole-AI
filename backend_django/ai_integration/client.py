"""
Servicio de IA para Django - Cliente de Phi-3.5 Vision-Instruct Q4
"""
import json
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError

from .models import AIServiceConfig, AIRequest, AIRequestLog

logger = logging.getLogger(__name__)


class AIServiceClient:
    """Cliente para comunicarse con el servicio Phi-3.5 Vision-Instruct"""
    
    def __init__(self):
        self.config = self._get_active_config()
        self.base_url = self.config.base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mole-AI-Django-Client/1.0'
        })
        
        # Add API key if configured
        if self.config.api_key:
            self.session.headers['Authorization'] = f'Bearer {self.config.api_key}'
    
    def _get_active_config(self):
        """Obtener configuración activa del servicio IA"""
        try:
            return AIServiceConfig.objects.filter(is_active=True).first()
        except AIServiceConfig.DoesNotExist:
            # Crear configuración por defecto
            return AIServiceConfig.objects.create(
                service_name="Mole AI Service",
                base_url="http://localhost:8001",
                model_name="microsoft/Phi-3.5-vision-instruct",
                is_active=True
            )
        except Exception as e:
            logger.error(f"Error getting AI service config: {e}")
            raise ValidationError(f"No se pudo configurar el servicio IA: {e}")
    
    async def diagnose_plant(self, plant_id: int, image_data: str, 
                            sensor_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enviar solicitud de diagnóstico al servicio Phi-3.5
        
        Args:
            plant_id: ID de la planta
            image_data: Imagen en formato base64
            sensor_data: Datos de sensores opcionales
            
        Returns:
            Respuesta del servicio IA
        """
        start_time = datetime.now()
        
        try:
            # Crear solicitud en la base de datos
            ai_request = await self._create_ai_request(plant_id, image_data, sensor_data)
            
            # Preparar payload para el servicio IA
            payload = {
                "imagen": image_data,
                "sensores": sensor_data or {},
                "plant_id": str(plant_id)
            }
            
            # Enviar solicitud al servicio IA
            response = self._send_request('/diagnostico', payload)
            
            # Procesar respuesta
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Actualizar solicitud con respuesta
            await self._update_ai_request(
                ai_request, 
                response, 
                processing_time,
                'completed'
            )
            
            # Crear resultado del diagnóstico
            diagnosis_result = await self._create_diagnosis_result(ai_request, response)
            
            logger.info(f"Diagnosis completed for plant {plant_id} in {processing_time}s")
            return {
                'request_id': ai_request.id,
                'diagnosis_id': diagnosis_result.id,
                'result': response,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in diagnosis for plant {plant_id}: {str(e)}")
            
            # Actualizar solicitud con error si existe
            if 'ai_request' in locals():
                await self._update_ai_request_with_error(
                    ai_request, 
                    str(e),
                    start_time,
                    'failed'
                )
            
            raise ValidationError(f"Error en el diagnóstico: {str(e)}")
    
    def _send_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enviar solicitud HTTP al servicio IA
        
        Args:
            endpoint: Endpoint del servicio
            payload: Datos a enviar
            
        Returns:
            Respuesta del servicio
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.config.timeout_seconds
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request error to {url}: {str(e)}")
            raise
    
    async def _create_ai_request(self, plant_id: int, image_data: str, 
                             sensor_data: Optional[Dict[str, Any]] = None) -> AIRequest:
        """Crear registro de solicitud IA"""
        from apps.plants_mgmt.models import Plant
        from apps.diagnostics_mgmt.models import SensorData as SensorDataModel
        from apps.ai_integration.models import PlantImage as PlantImageModel
        
        # Obtener planta y sensores
        try:
            plant = Plant.objects.get(id=plant_id)
            if sensor_data:
                # Usar sensores proporcionados
                pass
            else:
                # Obtener últimos sensores
                sensor_model = SensorDataModel.objects.filter(plant=plant).first()
                if sensor_model:
                    sensor_data = {
                        'ph': sensor_model.ph,
                        'humedad': sensor_model.humedad,
                        'temperatura': sensor_model.temperatura,
                        'uv': sensor_model.uv
                    }
                else:
                    sensor_data = {}
        except Exception as e:
            logger.error(f"Error getting plant/sensor data: {e}")
            raise ValidationError(f"No se pudo obtener datos de la planta: {e}")
        
        # Crear imagen
        image_model = PlantImageModel.objects.create(
            image_base64=image_data,
            filename=f"plant_{plant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
            format='jpeg'
        )
        
        # Crear solicitud IA
        ai_request = AIRequest.objects.create(
            plant=plant,
            image=image_model,
            sensor_data=SensorDataModel.objects.create(plant=plant, **sensor_data),
            status='processing',
            request_data={
                'plant_id': plant_id,
                'sensor_data': sensor_data,
                'has_image': bool(image_data),
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return ai_request
    
    async def _update_ai_request(self, ai_request: AIRequest, 
                                response_data: Dict[str, Any],
                                processing_time: float,
                                status: str) -> None:
        """Actualizar solicitud IA con respuesta exitosa"""
        ai_request.status = status
        ai_request.response_data = response_data
        ai_request.processing_time = processing_time
        ai_request.updated_at = datetime.now()
        ai_request.save()
    
    async def _update_ai_request_with_error(self, ai_request: AIRequest,
                                           error_message: str,
                                           start_time: datetime,
                                           status: str) -> None:
        """Actualizar solicitud IA con error"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        ai_request.status = status
        ai_request.error_message = error_message
        ai_request.processing_time = processing_time
        ai_request.updated_at = datetime.now()
        ai_request.save()
    
    async def _create_diagnosis_result(self, ai_request: AIRequest,
                                      response_data: Dict[str, Any]) -> 'ai_integration.DiagnosisResult':
        """Crear resultado del diagnóstico"""
        from apps.diagnostics_mgmt.models import DiagnosisResult
        
        # Extraer datos del response
        estado = response_data.get('estado', 'Atención')
        confianza = float(response_data.get('confianza', 0.5))
        especie = response_data.get('especie', '')
        sintomas = response_data.get('sintomas', [])
        diagnostico = response_data.get('diagnostico', '')
        recomendaciones = response_data.get('recomendaciones', [])
        fuentes = response_data.get('fuentes', [])
        
        diagnosis = DiagnosisResult.objects.create(
            plant=ai_request.plant,
            ai_request=ai_request,
            estado=estado,
            confianza=confianza,
            especie=especie,
            sintomas=sintomas,
            diagnostico=diagnostico,
            recomendaciones=recomendaciones,
            fuentes=fuentes,
            modelo_utilizado=response_data.get('modelo_utilizado', 'Phi-3.5 Vision-Instruct Q4'),
            tiempo_inferencia=response_data.get('tiempo_inferencia'),
            requiere_accion_humana=confianza < 0.85,
            datos_sensores=ai_request.sensor_data.__dict__,
            resultado_vision=response_data,
            contexto_conocimiento=response_data.get('conocimiento', {})
        )
        
        return diagnosis
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificar estado del servicio IA
        
        Returns:
            Estado del servicio
        """
        try:
            response = self._send_request('/health', {})
            
            # Actualizar health check en configuración
            self.config.last_health_check = datetime.now()
            self.config.health_status = 'healthy'
            self.config.save()
            
            return {
                'service': self.config.service_name,
                'status': 'healthy',
                'ai_service': response.get('status', 'unknown'),
                'last_check': self.config.last_health_check.isoformat(),
                'base_url': self.base_url
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            
            # Actualizar estado como unhealthy
            self.config.last_health_check = datetime.now()
            self.config.health_status = 'unhealthy'
            self.config.save()
            
            return {
                'service': self.config.service_name,
                'status': 'unhealthy',
                'error': str(e),
                'last_check': self.config.last_health_check.isoformat(),
                'base_url': self.base_url
            }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del servicio
        
        Returns:
            Estadísticas del servicio
        """
        try:
            stats = self._send_request('/system/metrics', {})
            
            return {
                'service': self.config.service_name,
                'ai_service_stats': stats,
                'local_requests_today': AIRequest.objects.filter(
                    created_at__date=datetime.now().date()
                ).count(),
                'successful_requests': AIRequest.objects.filter(
                    status='completed'
                ).count(),
                'failed_requests': AIRequest.objects.filter(
                    status='failed'
                ).count(),
                'avg_processing_time': AIRequest.objects.filter(
                    processing_time__isnull=False
                ).aggregate(
                    avg_time=models.Avg('processing_time')
                )['avg_time'] or 0,
                'last_health_check': self.config.last_health_check.isoformat(),
                'health_status': self.config.health_status
            }
            
        except Exception as e:
            logger.error(f"Error getting service stats: {str(e)}")
            return {
                'service': self.config.service_name,
                'error': str(e),
                'local_requests_today': AIRequest.objects.filter(
                    created_at__date=datetime.now().date()
                ).count(),
                'successful_requests': AIRequest.objects.filter(
                    status='completed'
                ).count(),
                'failed_requests': AIRequest.objects.filter(
                    status='failed'
                ).count(),
                'health_status': self.config.health_status
            }


# Instancia global del cliente
ai_client = AIServiceClient()