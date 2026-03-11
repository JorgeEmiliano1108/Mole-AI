from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, throttle_classes, authentication_classes
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status
import json
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated

from ..infrastructure.repositories.models import SensorLog, PlantKnowledge, AIDiagnostic
from plants.infrastructure.repositories.models import UserPlant
from ai_models.infrastructure.repositories.models import LLMRequest
from .throttles import LLMChatThrottle, DiagnosticsThrottle
from .serializers import (
    DiagnosticRequestSerializer,
    LLMChatRequestSerializer, SensorDataQuerySerializer,
    PlantKnowledgeQuerySerializer, SensorReadingSerializer, SensorBatchSerializer,
)
from ai_models.utils import consultar_phi_vision
from asgiref.sync import sync_to_async
from apps.authentication.infrastructure.authentication import HardwareAPIKeyAuthentication

# Import MoleAI client for HTTP fallback (same processing as WebSocket)
try:
    from ai_models.services import MoleAIClient, MoleAIServiceError
except Exception:
    MoleAIClient = None
    MoleAIServiceError = Exception


class HardwareOnlyPermission(BasePermission):
    """
    Permission class to allow only hardware IoT devices (M2M authentication).
    Rejects unauthenticated requests and JWT-authenticated human users.
    """
    def has_permission(self, request, view):
        return getattr(request.user, 'is_hardware_device', False)


def index_view(request):
    """
    Vista principal para la aplicación Mole AI
    """
    return render(request, 'index.html')


from django.db import transaction


@api_view(['POST'])
@authentication_classes([HardwareAPIKeyAuthentication])
@permission_classes([HardwareOnlyPermission])
def sensor_data_view(request):
    """
    M2M endpoint for single-timestamp telemetry from ESP32 or Edge Node.

    Auth: Header X-Hardware-Api-Key  (rejects JWT bearer tokens)

    Payload (Wide Table — matches sensor_logs columns):
    {
      "plant_id":        "<uuid>",
      "recorded_at":     "2026-03-07T10:30:00Z",   // optional, defaults to now
      "air_temperature": 27.4,
      "soil_humidity":   62.0,
      "uv_index":        5.2,
      "light_level":     450.0,
      "ph_level":        6.3                        // optional, TFLite CNN output
    }
    """
    serializer = SensorReadingSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Payload inválido", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = serializer.validated_data

    # Verify the plant_id is provisioned in user_plants
    if not UserPlant.objects.filter(id=data['plant_id']).exists():
        return Response(
            {"error": "plant_id no registrado",
             "detail": "El plant_id no existe en user_plants. El agricultor debe crear la planta primero."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        SensorLog.objects.create(
            plant_id=data['plant_id'],
            recorded_at=data['recorded_at'],
            soil_humidity=data.get('soil_humidity'),
            air_temperature=data.get('air_temperature'),
            uv_index=data.get('uv_index'),
            light_level=data.get('light_level'),
            ph_level=data.get('ph_level'),
        )
    except Exception as e:
        return Response(
            {"error": "Error al guardar en la base de datos", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {
            "status": "success",
            "plant_id": str(data['plant_id']),
            "recorded_at": data['recorded_at'].isoformat(),
            "registered": 1,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@authentication_classes([HardwareAPIKeyAuthentication])
@permission_classes([HardwareOnlyPermission])
def sensor_batch_view(request):
    """
    Bulk M2M endpoint for the Edge Node Store-and-Forward daemon.
    Accepts up to 500 readings per call.

    Payload: {"batch": [{plant_id, recorded_at?, air_temperature?, soil_humidity?, ...}, ...]}
    """
    serializer = SensorBatchSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Payload inválido", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    batch = serializer.validated_data['batch']

    # Verify all plant_ids in the batch are provisioned
    batch_plant_ids = {r['plant_id'] for r in batch}
    existing_ids = set(
        UserPlant.objects.filter(id__in=batch_plant_ids).values_list('id', flat=True)
    )
    unknown_ids = batch_plant_ids - existing_ids
    if unknown_ids:
        return Response(
            {"error": "plant_id(s) no registrados",
             "unknown_plant_ids": [str(uid) for uid in unknown_ids]},
            status=status.HTTP_404_NOT_FOUND,
        )

    logs_to_create = [
        SensorLog(
            plant_id=r['plant_id'],
            recorded_at=r['recorded_at'],
            soil_humidity=r.get('soil_humidity'),
            air_temperature=r.get('air_temperature'),
            uv_index=r.get('uv_index'),
            light_level=r.get('light_level'),
            ph_level=r.get('ph_level'),
        )
        for r in batch
    ]

    try:
        with transaction.atomic():
            created = SensorLog.objects.bulk_create(
                logs_to_create,
                batch_size=200,
            )
    except Exception as e:
        return Response(
            {"error": "Error en bulk insert", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {
            "status": "success",
            "total_sent": len(batch),
            "registered": len(created),
        },
        status=status.HTTP_201_CREATED,
    )



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
    API endpoint para registrar datos de sensores (legacy, JWT-authenticated).
    """
    try:
        data = json.loads(request.body)

        serializer = SensorReadingSerializer(data=data)
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid sensor data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        v = serializer.validated_data
        sensor_log = SensorLog.objects.create(
            plant_id=v['plant_id'],
            recorded_at=v['recorded_at'],
            soil_humidity=v.get('soil_humidity'),
            air_temperature=v.get('air_temperature'),
            uv_index=v.get('uv_index'),
            light_level=v.get('light_level'),
            ph_level=v.get('ph_level'),
        )

        return Response({
            'id': sensor_log.id,
            'message': 'Datos de sensor registrados correctamente',
            'recorded_at': sensor_log.recorded_at.isoformat()
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([LLMChatThrottle])
async def chat_fallback_view(request):
    """
    HTTP fallback for chat when WebSocket is unavailable (e.g., some serverless hosts)
    Espera JSON: { question, plant_id (opcional), image_base64 (opcional) }
    """
    if MoleAIClient is None:
        return Response({'error': 'AI client not available'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        data = json.loads(request.body)
        question = (data.get('question') or '').strip()
        if not question:
            return Response({'error': 'Question is required'}, status=status.HTTP_400_BAD_REQUEST)

        image_base64 = data.get('image_base64')
        data.get('plant_id')

        # Access sync properties via sync_to_async to avoid blocking the event loop
        session_key = await sync_to_async(lambda: request.session.session_key)()
        if not session_key:
            session_key = f'anonymous_{request.META.get("REMOTE_ADDR")}'

        user_id = await sync_to_async(lambda: (request.user.id if hasattr(request.user, 'id') and request.user.is_authenticated else None))()

        client = MoleAIClient()
        # Call async generate_chat_response
        result = await client.generate_chat_response(
            query=question,
            image_base64=image_base64,
            user_id=user_id,
            session_id=session_key
        )

        return Response({
            'type': 'response',
            'answer': result.get('answer'),
            'model_used': result.get('model_used'),
            'tokens_generated': result.get('tokens_generated'),
            'processing_time_ms': result.get('processing_time_ms'),
            'request_id': result.get('request_id')
        })

    except MoleAIServiceError as e:
        msg = str(e)
        # Detect timeout originating from aiohttp and return 504 with required JSON
        if 'timeout' in msg.lower() or 'timed out' in msg.lower() or 'timeout connecting' in msg.lower():
            return Response({
                'error': 'El servidor de IA está tardando demasiado en analizar la planta. Por favor, intenta de nuevo.',
                'status': 'timeout'
            }, status=504)
        return Response({'error': msg}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
