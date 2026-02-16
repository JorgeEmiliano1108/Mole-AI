from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
from datetime import datetime, timedelta
import random
import requests


from ..infrastructure.repositories.models import SensorLog, PlantKnowledge, AIDiagnostic
from ai_models.infrastructure.repositories.models import LLMRequest, CNNInference
from .throttles import LLMChatThrottle, DiagnosticsThrottle, SensorDataThrottle
from .serializers import (
    SensorLogSerializer, DiagnosticRequestSerializer, 
    LLMChatRequestSerializer, SensorDataQuerySerializer,
    PlantKnowledgeQuerySerializer
)
from ai_models.utils import consultar_phi_vision


def index_view(request):
    """
    Vista principal para la aplicación Mole AI
    """
    return render(request, 'index.html')


@api_view(['GET'])
def sensor_data_view(request):
    """
    API endpoint para obtener datos de sensores
    BUILDER FIX: Dev Mode support
    """
    from django.conf import settings
    
    # Check for authentication OR Dev Mode
    if not request.user.is_authenticated:
        # Dev mode: Allow if DEBUG is True AND specific query param is present
        is_dev_access = settings.DEBUG and request.GET.get('dev_mode') == 'true'
        if not is_dev_access:
            return Response(
                {'detail': 'Authentication credentials were not provided.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
    try:
        # Validar parámetros de consulta con serializer
        query_serializer = SensorDataQuerySerializer(data=request.GET)
        if not query_serializer.is_valid():
            return Response({
                'error': 'Invalid query parameters',
                'details': query_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener parámetros validados
        hours_ago = query_serializer.validated_data['hours_ago']
        limit = query_serializer.validated_data['limit']
        sensor_types = query_serializer.validated_data['sensor_types']
        
        # Calcular fecha límite
        since_date = datetime.now() - timedelta(hours=hours_ago)
        
        # Construir query
        queryset = SensorLog.objects.filter(
            timestamp__gte=since_date
        )
        
        if sensor_types:
            queryset = queryset.filter(sensor_type__in=sensor_types)
        
        # Ordenar y limitar
        sensor_logs = queryset.order_by('-timestamp')[:limit]
        
        # Serializar datos
        data = []
        for log in sensor_logs:
            data.append({
                'id': log.id,
                'device_id': log.device_id,
                'sensor_type': log.sensor_type,
                'value': log.value,
                'unit': log.unit,
                'plant_id': log.plant_id,
                'timestamp': log.timestamp.isoformat(),
                'location_x': log.location_x,
                'location_y': log.location_y,
            })
        
        return Response({
            'results': data,
            'count': len(data),
            'hours_ago': hours_ago,
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Error obteniendo datos de sensores'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([DiagnosticsThrottle])
def diagnostic_view(request):
    """
    API endpoint para crear diagnóstico con Phi-3.5 Vision (Generativo)
    """
    try:
        # 1. Validación de datos (sin cambios)
        data = {
            'image': request.FILES.get('image'),
            'plant_id': request.POST.get('plant_id', 'desconocida'),
            'model_type': request.POST.get('model_type', 'disease_detection')
        }
        
        diagnostic_serializer = DiagnosticRequestSerializer(data=data)
        if not diagnostic_serializer.is_valid():
            return Response({
                'error': 'Solicitud inválida',
                'details': diagnostic_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Obtener datos validados
        image_file = diagnostic_serializer.validated_data['image']
        plant_id = diagnostic_serializer.validated_data.get('plant_id', 'desconocida')
        
        # 3. Prompt optimizado para Phi-3.5 Vision
        prompt = (
            "Actúa como un agrónomo experto. Analiza esta imagen. "
            "1. Identifica la especie de la planta. "
            "2. Describe detalladamente cualquier síntoma de enfermedad, plaga o deficiencia. "
            "3. Si está sana, confírmalo. "
            "4. Recomienda un tratamiento específico si es necesario. "
            "Responde en español."
        )
        
        # 4. Llamada a Phi-3.5 Vision
        print(f"🤖 Analizando imagen de planta {plant_id} con Phi-3.5...")
        resultado_ia = consultar_phi_vision(image_file, prompt)
        
        # 5. Verificar respuesta de HF
        if isinstance(resultado_ia, dict) and "error" in resultado_ia:
            return Response({
                'error': resultado_ia['error'],
                'message': 'El servicio de IA no pudo procesar la imagen.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 6. Procesamiento del texto generado
        analisis_completo = str(resultado_ia)
        
        # 7. Heurística para determinar severidad
        texto_lower = analisis_completo.lower()
        severity = 'medium'  # Valor por defecto
        if any(x in texto_lower for x in ['sana', 'saludable', 'vigorosa', 'sin plagas']):
            severity = 'low'
        elif any(x in texto_lower for x in ['muerte', 'grave', 'urgente', 'crítico']):
            severity = 'high'
        
        # 8. Guardado en base de datos (adaptado a modelo generativo)
        diagnostic = AIDiagnostic.objects.create(
            user=request.user,
            plant_id=plant_id,
            diagnostic_type='generative_vision',
            
            # Como no hay etiqueta corta, usamos un título genérico
            condition_name="Análisis Phi-3.5 Vision",
            
            # Aquí guardamos toda la explicación del modelo
            condition_description=analisis_completo,
            
            severity=severity,
            ai_model_used='microsoft/Phi-3.5-vision-instruct',
            confidence_score=1.0,  # Los modelos generativos no dan confidence score numérico
            processing_time_ms=resultado_ia.get('processing_time_ms', 0) if isinstance(resultado_ia, dict) else 0,
            image_url=image_file.name,
            
            # Guardamos el texto crudo en el campo JSON por si acaso
            top_prediction={"raw_output": analisis_completo},
            predictions=[],  # El modelo ya da el análisis en texto
            confidence_scores=[],
            
            status='completed',
            completed_at=datetime.now()
        )
        
        # 9. Respuesta al frontend (mejorada)
        return Response({
            'id': diagnostic.id,
            'condition_name': diagnostic.condition_name,
            'analysis': analisis_completo,  # Enviamos el texto completo
            'severity': diagnostic.severity,
            'created_at': diagnostic.created_at.isoformat()
        })
        
    except requests.exceptions.Timeout:
        return Response({
            'error': 'Timeout en API de Hugging Face',
            'message': 'El análisis está tomando demasiado tiempo'
        }, status=status.HTTP_408_REQUEST_TIMEOUT)
    except requests.exceptions.ConnectionError:
        return Response({
            'error': 'Error de conexión con Hugging Face',
            'message': 'No se puede conectar al servicio de IA'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Error procesando diagnóstico'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def diagnostic_history_view(request):
    """
    API endpoint para obtener historial de diagnósticos
    """
    try:
        limit = int(request.GET.get('limit', 20))
        
        diagnostics = AIDiagnostic.objects.filter(
            user=request.user
        ).order_by('-created_at')[:limit]
        
        data = []
        for diag in diagnostics:
            data.append({
                'id': diag.id,
                'plant_id': diag.plant_id,
                'condition_name': diag.condition_name,
                'condition_description': diag.condition_description,
                'severity': diag.severity,
                'confidence_score': diag.confidence_score,
                'status': diag.status,
                'created_at': diag.created_at.isoformat(),
                'completed_at': diag.completed_at.isoformat() if diag.completed_at else None,
            })
        
        return Response({
            'results': data,
            'count': len(data)
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Error obteniendo historial de diagnósticos'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sensor_log_view(request):
    """
    API endpoint para registrar datos de sensores
    """
    try:
        data = json.loads(request.body)
        
        # Validar con serializer
        sensor_serializer = SensorLogSerializer(data=data)
        if not sensor_serializer.is_valid():
            return Response({
                'error': 'Invalid sensor data',
                'details': sensor_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear registro de sensor con datos validados
        sensor_log = SensorLog.objects.create(
            user=request.user,
            **sensor_serializer.validated_data,
            timestamp=datetime.now()
        )
        
        return Response({
            'id': sensor_log.id,
            'message': 'Datos de sensor registrados correctamente',
            'timestamp': sensor_log.timestamp.isoformat()
        })
        
    except json.JSONDecodeError:
        return Response({
            'error': 'JSON inválido'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Error registrando datos de sensor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def plant_knowledge_view(request):
    """
    API endpoint para consultar base de conocimiento de plantas
    """
    try:
        # Validar parámetros de consulta
        query_serializer = PlantKnowledgeQuerySerializer(data=request.GET)
        if not query_serializer.is_valid():
            return Response({
                'error': 'Invalid query parameters',
                'details': query_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        plant_species = query_serializer.validated_data.get('plant_species')
        knowledge_type = query_serializer.validated_data.get('knowledge_type')
        
        queryset = PlantKnowledge.objects.all()
        
        if plant_species:
            queryset = queryset.filter(plant_species__icontains=plant_species)
        if knowledge_type:
            queryset = queryset.filter(knowledge_type=knowledge_type)
        
        knowledge = queryset.order_by('-confidence_score')[:20]
        
        data = []
        for item in knowledge:
            data.append({
                'id': item.id,
                'title': item.title,
                'content': item.content,
                'knowledge_type': item.knowledge_type,
                'plant_species': item.plant_species,
                'plant_genus': item.plant_genus,
                'confidence_score': item.confidence_score,
                'language': item.language,
            })
        
        return Response({
            'results': data,
            'count': len(data)
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Error consultando base de conocimiento'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([LLMChatThrottle])
def llm_chat_view(request):
    """
    API endpoint para chat con LLM
    """
    try:
        data = json.loads(request.body)
        
        # Validar con serializer
        chat_serializer = LLMChatRequestSerializer(data=data)
        if not chat_serializer.is_valid():
            return Response({
                'error': 'Invalid chat request',
                'details': chat_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener datos validados
        prompt = chat_serializer.validated_data['prompt']
        request_type = chat_serializer.validated_data['request_type']
        plant_species = chat_serializer.validated_data.get('plant_species')
        
        # Simular respuesta de LLM
        responses = {
            'manzanilla': 'La manzanilla (Matricaria chamomilla) es una planta medicinal conocida por sus propiedades antiinflamatorias y calmantes. Se usa para tratar trastornos digestivos, ansiedad y problemas de sueño.',
            'sabila': 'El sábila (Aloe vera) es excelente para quemaduras, heridas y problemas de piel. También tiene propiedades laxantes suaves y ayuda en la digestión.',
            'menta': 'La menta (Mentha spicata) es ideal para problemas digestivos, dolores de cabeza y como descongestionante respiratorio. Su aceite esencial tiene propiedades antibacterianas.',
            'lavanda': 'La lavanda (Lavandula angustifolia) es famosa por sus propiedades relajantes. Se usa para tratar ansiedad, insomnio y problemas de piel.',
            'default': 'Soy Mole-IA, tu asistente especializado en flora mexicana. Puedo ayudarte con información sobre cuidado de plantas, propiedades medicinales, recetas tradicionales y monitoreo agrícola.'
        }
        
        response_text = responses.get(plant_species, responses['default'])
        
        # Crear registro de LLM request
        llm_request = LLMRequest.objects.create(
            user=request.user,
            session_id=request.session.session_key or 'anonymous',
            request_type=request_type,
            prompt=prompt,
            context={'plant_species': plant_species} if plant_species else {},
            model_name='mole-ai-v1',
            temperature=0.7,
            max_tokens=1000,
            response=response_text,
            processing_time_ms=random.randint(200, 1000),
            status='completed',
            completed_at=datetime.now()
        )
        
        return Response({
            'id': llm_request.id,
            'response': response_text,
            'request_type': request_type,
            'processing_time_ms': llm_request.processing_time_ms,
            'created_at': llm_request.created_at.isoformat()
        })
        
    except json.JSONDecodeError:
        return Response({
            'error': 'JSON inválido'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Error procesando solicitud LLM'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check_view(request):
    """
    API endpoint para verificar salud del sistema
    """
    return Response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.1',
        'service': 'Mole AI Backend'
    })
