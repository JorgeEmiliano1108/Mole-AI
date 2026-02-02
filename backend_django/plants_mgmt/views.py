from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

from .models import Plant, SensorData, Diagnosis, PlantImage
from .serializers import (
    PlantSerializer, 
    SensorDataSerializer, 
    DiagnosisSerializer,
    PlantImageSerializer,
    DiagnosisRequestSerializer,
    EmergencyDiagnosisRequestSerializer,
    ImageAnalysisRequestSerializer
)
from ..ai_integration.adapters.ai_client import ai_client, handle_ai_errors

logger = logging.getLogger(__name__)

class PlantViewSet(viewsets.ModelViewSet):
    """ViewSet para el modelo Plant"""
    
    queryset = Plant.objects.all()
    serializer_class = PlantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar plantas por usuario actual con optimización"""
        return Plant.objects.filter(owner=self.request.user)\
                        .select_related('owner')\
                        .prefetch_related(
                            'diagnoses__sensor_data',
                            'sensor_readings',
                            'images'
                        )
    
    def perform_create(self, serializer):
        """Asignar usuario actual al crear planta"""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    @handle_ai_errors
    async def analyze_image(self, request, pk=None):
        """Analiza imagen de la planta usando servicio de IA"""
        plant = self.get_object()
        
        # Validar datos de entrada
        serializer = ImageAnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        image_file = serializer.validated_data['image']
        analysis_type = serializer.validated_data['analysis_type']
        plant_context = serializer.validated_data.get('plant_context', '')
        
        try:
            # 1. Guardar imagen
            plant_image = PlantImage.objects.create(
                plant=plant,
                image=image_file,
                image_type=analysis_type
            )
            
            # 2. Analizar imagen con servicio de visión
            vision_result = await ai_client.analyze_plant_image(
                image_file=image_file,
                analysis_type=analysis_type,
                plant_context=plant_context
            )
            
            # 3. Guardar resultado del análisis
            plant_image.analysis_result = vision_result.get('data', {})
            plant_image.save()
            
            # 4. Actualizar estado de la planta si es necesario
            if vision_result.get('success'):
                analysis_data = vision_result['data']
                new_status = analysis_data.get('health_status', 'healthy')
                if new_status != plant.status:
                    plant.status = new_status
                    plant.save()
            
            return Response({
                'success': True,
                'image_id': plant_image.id,
                'analysis_result': vision_result
            })
            
        except Exception as e:
            logger.error(f"Error analizando imagen: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    @handle_ai_errors
    async def diagnose(self, request, pk=None):
        """Realiza diagnóstico completo de la planta"""
        plant = self.get_object()
        
        # Validar datos de entrada
        serializer = DiagnosisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # 1. Procesar datos de sensores si se proporcionan
            sensor_data_dict = serializer.validated_data.get('sensor_data')
            if sensor_data_dict:
                sensor_data_dict['plant'] = plant.id
                sensor_serializer = SensorDataSerializer(data=sensor_data_dict)
                sensor_serializer.is_valid(raise_exception=True)
                sensor_data_obj = sensor_serializer.save()
            else:
                # Usar datos de sensores más recientes (optimizado)
                sensor_data_obj = plant.sensor_readings.select_related('plant').first()
            
            # 2. Procesar imagen si se proporciona
            vision_result = None
            image_file = serializer.validated_data.get('image')
            if image_file:
                analysis_type = serializer.validated_data.get('analysis_type', 'rgb')
                plant_context = serializer.validated_data.get('plant_context', '')
                
                vision_result = await ai_client.analyze_plant_image(
                    image_file=image_file,
                    analysis_type=analysis_type,
                    plant_context=plant_context
                )
            
            # 3. Preparar datos para diagnóstico RAG
            diagnosis_request = {
                'sensor_data': {
                    'device_id': sensor_data_obj.device_id if sensor_data_obj else 'unknown',
                    'humidity': sensor_data_obj.humidity if sensor_data_obj else 0,
                    'temperature': sensor_data_obj.temperature if sensor_data_obj else 0,
                    'ph': sensor_data_obj.ph if sensor_data_obj else 0,
                    'uv_index': sensor_data_obj.uv_index if sensor_data_obj else 0,
                    'soil_moisture': sensor_data_obj.soil_moisture if sensor_data_obj else 0,
                    'plant_id': str(plant.id),
                    'timestamp': sensor_data_obj.timestamp.isoformat() if sensor_data_obj else timezone.now().isoformat()
                },
                'vision_results': vision_result.get('data') if vision_result else None,
                'plant_context': serializer.validated_data.get('plant_context', '')
            }
            
            # 4. Obtener diagnóstico del servicio RAG
            diagnosis_result = await ai_client.diagnose_plant(**diagnosis_request)
            
            # 5. Guardar diagnóstico en base de datos
            if diagnosis_result.get('success'):
                diagnosis_data = diagnosis_result['data']
                diagnosis = Diagnosis.objects.create(
                    plant=plant,
                    sensor_data=sensor_data_obj,
                    vision_analysis=vision_result.get('data') if vision_result else None,
                    rag_context=diagnosis_data.get('rag_context', []),
                    diagnosis_text=diagnosis_data.get('diagnosis', ''),
                    treatment_plan=diagnosis_data.get('treatment_plan', []),
                    urgency_level=diagnosis_data.get('urgency_level', 'low'),
                    confidence=diagnosis_data.get('confidence', 0.0),
                    recommendations=diagnosis_data.get('recommendations', []),
                    processing_time=diagnosis_result.get('processing_time', 0.0)
                )
                
                # 6. Actualizar estado de la planta
                new_status = self._map_urgency_to_status(diagnosis_data.get('urgency_level', 'low'))
                plant.status = new_status
                plant.save()
                
                return Response({
                    'success': True,
                    'diagnosis_id': diagnosis.id,
                    'diagnosis_result': DiagnosisSerializer(diagnosis).data
                })
            else:
                return Response({
                    'success': False,
                    'error': diagnosis_result.get('error_message', 'Error desconocido')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error en diagnóstico: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    @handle_ai_errors
    async def emergency_diagnose(self, request, pk=None):
        """Diagnóstico de emergencia"""
        plant = self.get_object()
        
        # Validar datos de entrada
        serializer = EmergencyDiagnosisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Procesar datos de sensores (requerido)
            sensor_data_dict = serializer.validated_data['sensor_data']
            sensor_data_dict['plant'] = plant.id
            sensor_serializer = SensorDataSerializer(data=sensor_data_dict)
            sensor_serializer.is_valid(raise_exception=True)
            sensor_data_obj = sensor_serializer.save()
            
            # Procesar imagen si se proporciona
            vision_result = None
            image_file = serializer.validated_data.get('image')
            if image_file:
                analysis_type = serializer.validated_data.get('analysis_type', 'rgb')
                vision_result = await ai_client.analyze_plant_image(
                    image_file=image_file,
                    analysis_type=analysis_type
                )
            
            # Preparar solicitud de emergencia
            emergency_request = {
                'sensor_data': {
                    'device_id': sensor_data_obj.device_id,
                    'humidity': sensor_data_obj.humidity,
                    'temperature': sensor_data_obj.temperature,
                    'ph': sensor_data_obj.ph,
                    'uv_index': sensor_data_obj.uv_index,
                    'soil_moisture': sensor_data_obj.soil_moisture,
                    'plant_id': str(plant.id),
                    'timestamp': sensor_data_obj.timestamp.isoformat()
                },
                'vision_results': vision_result.get('data') if vision_result else None
            }
            
            # Obtener diagnóstico de emergencia
            emergency_result = await ai_client.emergency_diagnosis(**emergency_request)
            
            # Guardar diagnóstico de emergencia
            if emergency_result.get('success'):
                diagnosis_data = emergency_result['data']
                diagnosis = Diagnosis.objects.create(
                    plant=plant,
                    sensor_data=sensor_data_obj,
                    vision_analysis=vision_result.get('data') if vision_result else None,
                    rag_context=diagnosis_data.get('rag_context', []),
                    diagnosis_text=diagnosis_data.get('diagnosis', ''),
                    treatment_plan=diagnosis_data.get('treatment_plan', []),
                    urgency_level='critical',  # Forzar urgencia crítica
                    confidence=diagnosis_data.get('confidence', 0.0),
                    recommendations=diagnosis_data.get('recommendations', []),
                    processing_time=emergency_result.get('processing_time', 0.0)
                )
                
                # Actualizar estado de la planta a crítico
                plant.status = 'multiple_issues'
                plant.save()
                
                return Response({
                    'success': True,
                    'diagnosis_id': diagnosis.id,
                    'emergency': True,
                    'diagnosis_result': DiagnosisSerializer(diagnosis).data
                })
            else:
                return Response({
                    'success': False,
                    'error': emergency_result.get('error_message', 'Error en emergencia')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error en diagnóstico de emergencia: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _map_urgency_to_status(self, urgency_level):
        """Mapea nivel de urgencia a estado de planta"""
        mapping = {
            'low': 'healthy',
            'medium': 'nutrient_deficiency',
            'high': 'stress_water',
            'critical': 'multiple_issues'
        }
        return mapping.get(urgency_level, 'healthy')

class SensorDataViewSet(viewsets.ModelViewSet):
    """ViewSet para el modelo SensorData"""
    
    queryset = SensorData.objects.all()
    serializer_class = SensorDataSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar datos por plantas del usuario con optimización"""
        return SensorData.objects.filter(plant__owner=self.request.user)\
                           .select_related('plant', 'plant__owner')\
                           .order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Obtener datos más recientes por planta"""
        plant_id = request.query_params.get('plant_id')
        if not plant_id:
            return Response({
                'error': 'Se requiere plant_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            plant = get_object_or_404(Plant, id=plant_id, owner=request.user)
            latest_data = plant.sensor_readings.first()
            
            if latest_data:
                serializer = self.get_serializer(latest_data)
                return Response(serializer.data)
            else:
                return Response({
                    'message': 'No hay datos de sensores para esta planta'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DiagnosisViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para diagnósticos"""
    
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar diagnósticos por plantas del usuario con optimización"""
        return Diagnosis.objects.filter(plant__owner=self.request.user)\
                           .select_related('plant', 'sensor_data', 'plant__owner')\
                           .order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Obtener diagnóstico más reciente por planta"""
        plant_id = request.query_params.get('plant_id')
        if not plant_id:
            return Response({
                'error': 'Se requiere plant_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            plant = get_object_or_404(Plant, id=plant_id, owner=request.user)
            latest_diagnosis = plant.diagnoses.first()
            
            if latest_diagnosis:
                serializer = self.get_serializer(latest_diagnosis)
                return Response(serializer.data)
            else:
                return Response({
                    'message': 'No hay diagnósticos para esta planta'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)