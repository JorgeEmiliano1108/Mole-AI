# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
import json
import os
import math
import logging
import random
import uuid
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, cast, List

from django.shortcuts import render
from django.db import transaction
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, throttle_classes, authentication_classes
from rest_framework.permissions import BasePermission, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import async_to_sync

# Repositorios y Modelos
from .models import (
    SensorLog, BotanicalKnowledge, AIDiagnostic, 
    DiagnosticoGeolocalizado, FeedbackTicket, Device
)
from apps.plants.models import UserPlant
from apps.ai_models.models import LLMRequest
from apps.authentication.infrastructure.authentication import HardwareAPIKeyAuthentication

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def revoke_device_token(request, id):
    """
    Revoca (desactiva) un dispositivo IoT.
    Soft‑delete: marca `is_active=False` sin borrar datos históricos.
    """
    try:
        device = Device.objects.get(pk=id)
    except Device.DoesNotExist:
        return Response(status=404)
    device.is_active = False
    device.save(update_fields=['is_active'])
    return Response(status=204)

# Servicios y Serializers
from .throttles import LLMChatThrottle, DiagnosticsThrottle, SensorDataThrottle
from .serializers import (
    DiagnosticRequestSerializer, LLMChatRequestSerializer, 
    SensorReadingSerializer, SensorBatchSerializer,
    FeedbackTicketCreateSerializer, FeedbackTicketResponseSerializer,
    SensorDataPatchSerializer, PlantKnowledgeQuerySerializer
)
from apps.ai_models.utils import consultar_phi_vision

# Cliente MoleAI (RAG)
try:
    from apps.ai_models.services import MoleAIClient, MoleAIServiceError
except Exception:
    MoleAIClient = None
    MoleAIServiceError = Exception

logger = logging.getLogger(__name__)

# --- PERMISOS ---
class HardwareOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'is_hardware_device', False)

# --- VISTA INDEX ---
def index_view(request):
    context = {
        'SUPABASE_URL': getattr(settings, 'SUPABASE_URL', '') or '',
        'SUPABASE_KEY': os.getenv('SUPABASE_KEY', ''),
    }
    return render(request, 'index.html', context)

# --- TELEMETRÍA IOT (M2M) ---
@api_view(['POST'])
@authentication_classes([HardwareAPIKeyAuthentication])
@permission_classes([HardwareOnlyPermission])
@throttle_classes([SensorDataThrottle])
def sensor_data_view(request):
    serializer = SensorReadingSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": "Payload inválido", "details": serializer.errors}, status=400)

    # Cast explícito para silenciar el error de "type empty"
    v_data = cast(Dict[str, Any], serializer.validated_data)
    
    # [RF-IOTSEC-001] Protección Anti-Replay (ETSI EN 303 645)
    recorded_at = v_data.get('recorded_at')
    if recorded_at:
        delta_seconds = abs((timezone.now() - recorded_at).total_seconds())
        if delta_seconds > 300:
            logger.warning(f"Bloqueo Anti-Replay: Delta de {delta_seconds}s detectado en ESP32.")
            return Response({"error": "Replay attack protection: Timestamp out of sync (> 300s)"}, status=403)

    
    if not UserPlant.objects.filter(id=v_data['plant_id']).exists():
        return Response({"error": "plant_id no registrado"}, status=404)

    try:
        SensorLog.objects.create(
            plant_id=v_data['plant_id'],
            recorded_at=v_data['recorded_at'],
            soil_humidity=v_data.get('soil_humidity'),
            air_temperature=v_data.get('air_temperature'),
            uv_index=v_data.get('uv_index'),
            light_level=v_data.get('light_level'),
            ph_level=v_data.get('ph_level'),
        )
        return Response({"status": "success", "registered": 1}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([HardwareAPIKeyAuthentication])
@permission_classes([HardwareOnlyPermission])
def sensor_batch_view(request):
    serializer = SensorBatchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    v_data = cast(Dict[str, Any], serializer.validated_data)
    batch = cast(List[Dict[str, Any]], v_data['batch'])
    
    # [RF-IOTSEC-001] Protección Anti-Replay para Lotes
    if batch and 'recorded_at' in batch[0]:
        delta_seconds = abs((timezone.now() - batch[0]['recorded_at']).total_seconds())
        if delta_seconds > 300:
            logger.warning(f"Bloqueo Anti-Replay en Lote: Delta de {delta_seconds}s detectado.")
            return Response({"error": "Replay attack protection in batch: Timestamp out of sync (> 300s)"}, status=403)

    
    logs = [SensorLog(**item) for item in batch]
    with transaction.atomic():
        created = SensorLog.objects.bulk_create(logs)
    return Response({"status": "success", "registered": len(created)}, status=201)

@api_view(['PATCH'])
@authentication_classes([HardwareAPIKeyAuthentication])
@permission_classes([HardwareOnlyPermission])
def sensor_data_patch_view(request, pk):
    try:
        log = SensorLog.objects.get(pk=pk)
        serializer = SensorDataPatchSerializer(log, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "updated"})
    except SensorLog.DoesNotExist:
        return Response(status=404)

class EdgeNodeIngestView(APIView):
    """
    POST /api/v1/sensor-data/edge-batch/
    Ingests the compact ESP32 telemetry frame and demultiplexes into
    AmbientReading + SoilReading (1:N relational schema).

    Decisions: A1=partial success, A2=ACID, A3=freeze SensorLog, A4=future-only anti-replay.
    """
    permission_classes = [AllowAny]  # Temporal — will use HardwareOnlyPermission in production

    def post(self, request):
        from .models import Device, HardwareBinding, AmbientReading, SoilReading
        from .serializers import EdgeFrameSerializer

        # ── Auth: resolve Device by Bearer token ────────────────────────
        auth_header = request.headers.get('Authorization', '').replace('Bearer ', '')
        device = Device.objects.filter(auth_token=auth_header).first()
        if not device or not getattr(device, 'is_active', True):
            return Response({"error": "Device not found or unauthorized"}, status=401)

        # ── Validate compact contract ───────────────────────────────────
        serializer = EdgeFrameSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "Invalid frame", "details": serializer.errors}, status=400)

        v = serializer.validated_data
        naive_dt = datetime.fromtimestamp(v['ts'])
        recorded_at = timezone.make_aware(naive_dt)
        ambient_data = v.get('a')  # Already expanded by serializer
        soil_items = v.get('s', [])

        soil_mapped = 0
        orphaned_pins = []

        # ── A2: ACID — entire frame succeeds or rolls back ─────────────
        with transaction.atomic():
            # Heartbeat (ISSUE-01)
            update_fields = {'last_seen': timezone.now(), 'status': 'online'}
            if v.get('ri'):
                update_fields['report_interval_minutes'] = v['ri']
            Device.objects.filter(pk=device.pk).update(**update_fields)

            # Ambient demux
            if ambient_data:
                AmbientReading.objects.create(
                    device=device,
                    recorded_at=recorded_at,
                    **ambient_data
                )

            # Soil demux (A1: partial success — skip unbound pins, report them)
            if soil_items:
                bindings_by_pin = {
                    b.hardware_pin: b
                    for b in HardwareBinding.objects.filter(device=device)
                }

                soil_objects = []
                for item in soil_items:
                    binding = bindings_by_pin.get(str(item['p']))
                    if binding:
                        soil_objects.append(
                            SoilReading(
                                binding=binding,
                                recorded_at=recorded_at,
                                soil_humidity=item['v']
                            )
                        )
                    else:
                        orphaned_pins.append(str(item['p']))

                if soil_objects:
                    SoilReading.objects.bulk_create(soil_objects)
                    soil_mapped = len(soil_objects)

                if orphaned_pins:
                    logger.warning(
                        "EdgeIngest: device=%s orphaned pins: %s",
                        device.pk, orphaned_pins
                    )

        return Response({
            "status": "ingested",
            "ambient": ambient_data is not None,
            "soil_mapped": soil_mapped,
            "orphaned_pins": orphaned_pins,
        })

# --- INTELIGENCIA ARTIFICIAL Y DIAGNÓSTICOS ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def diagnostic_view(request):
    """
    POST /api/v1/diagnostics/
    Envía imagen a MS1 de forma asíncrona via Celery.
    No bloquea el request - el frontend hace polling del task_id.
    """
    import tempfile
    import os
    from apps.ai_models.tasks import analyze_vision_async
    
    serializer = DiagnosticRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    v_data = serializer.validated_data
    
    image_file = v_data.get('image')
    if not image_file:
        return Response({"error": "Imagen requerida"}, status=400)
    
    from django.utils._os import safe_join
    temp_dir = tempfile.gettempdir()
    # Use Django's safe_join to prevent path traversal
    temp_path = safe_join(temp_dir, f"diagnostic_{request.user.id}_{image_file.name}")
    
    with open(temp_path, 'wb+') as f:
        for chunk in image_file.chunks():
            f.write(chunk)
    
    auth_header = request.headers.get('Authorization', '')
    task = analyze_vision_async.delay(
        temp_path,
        auth_header,
        user_id=request.user.id,
        plant_id=v_data.get('plant_id')
    )
    
    return Response({
        "status": "processing",
        "task_id": task.id,
        "message": "Diagnóstico en cola. Consulta /api/v1/ai/vision/status/{task_id} para ver el resultado."
    }, status=202)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def diagnostic_history_view(request):
    limit = int(request.GET.get('limit', 20))
    diagnostics = AIDiagnostic.objects.select_related('user').filter(user=request.user).order_by('-analyzed_at')[:limit]
    data = [{
        'id': str(d.id), 
        'plant_id': d.plant_id, 
        'condition': d.diagnosis_label,
        'analyzed_at': d.analyzed_at.isoformat()
    } for d in diagnostics]
    return Response({'results': data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_diagnostic_pdf(request, id):
    """
    GET /api/v1/diagnostics/{id}/download/
    Dispatches PDF generation to Celery (reports_queue).
    Returns 202 with task_id — frontend polls /api/v1/tasks/status/{task_id}/
    for the presigned download URL.
    """
    from apps.core.tasks import generate_pdf_async

    task = generate_pdf_async.delay(
        diagnostic_id=str(id),
        user_id=request.user.id,
    )

    return Response({
        "status": "processing",
        "task_id": task.id,
        "message": "PDF en generación. Consulta el estado en poll_url.",
        "poll_url": f"/api/v1/tasks/status/{task.id}/",
    }, status=202)

# --- MAPAS Y HOTSPOTS ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def map_hotspots_view(request):
    qs = DiagnosticoGeolocalizado.objects.select_related('user', 'diagnostic').all()[:100]
    results = []
    for r in qs:
        sev = r.severity
        # Normalizar 'critical' a 'high' para que el frontend lo renderice como rojo
        if sev == 'critical':
            sev = 'high'
        results.append({
            'lat': r.latitude,
            'lng': r.longitude,
            'severity': sev,
            'species': r.condition_name
        })
    return Response({'hotspots': results})

@api_view(['GET'])
@permission_classes([AllowAny]) # Accesible desde Leaflet (Frontend)
def openweather_tile_proxy(request, layer, z, x, y):
    """
    Proxy seguro para capas de OpenWeather (Temp, Precipitación, etc).
    Evita exponer la API KEY en el JS del frontend.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        return HttpResponse(status=501)
        
    url = f"https://tile.openweathermap.org/map/{layer}/{z}/{x}/{y}.png?appid={api_key}"
    try:
        r = requests.get(url, stream=True, timeout=5)
        if r.status_code == 200:
            return HttpResponse(r.raw, content_type="image/png")
        return HttpResponse(status=r.status_code)
    except requests.exceptions.RequestException:
        return HttpResponse(status=502)

@api_view(['GET'])
@permission_classes([AllowAny])
def current_weather_proxy(request):
    """Proxy seguro para obtener clima actual por coordenadas."""
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    if not lat or not lon:
        return Response({'error': 'lat and lon are required'}, status=400)
    
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        return Response({'error': 'API key not configured'}, status=501)
        
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=es"
    try:
        r = requests.get(url, timeout=5)
        return Response(r.json(), status=r.status_code)
    except requests.exceptions.RequestException as e:
        return Response({'error': str(e)}, status=502)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def diagnosticos_geolocalizados_list(request):
    qs = DiagnosticoGeolocalizado.objects.select_related('user', 'diagnostic').filter(user=request.user)[:50]
    return Response({'results': [{'id': r.id, 'condition': r.condition_name} for r in qs]})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def diagnosticos_geolocalizados_create(request):
    return Response({"status": "created"}, status=201)

# ---------------------------------------------------------------------------
# IoT NODE – endpoint de creación
# ---------------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def iot_node_create(request):
    from .serializers import IoTNodeCreateSerializer
    ser = IoTNodeCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    ser.save(user=request.user)
    return Response({'status':'created','node':ser.data}, status=201)

# --- CHAT Y RAG ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([LLMChatThrottle])
def chat_fallback_view(request):
    """
    POST /api/v1/chat/fallback/
    Dispatches RAG chat to Celery (chat_queue).
    Returns 202 with task_id — frontend polls /api/v1/tasks/status/{task_id}/
    for the chat answer.
    """
    if MoleAIClient is None:
        return Response({'error': 'AI client not available'}, status=500)

    question = cast(str, request.data.get('question', '')).strip()
    if not question:
        return Response({'error': 'La pregunta no puede estar vacía.'}, status=400)

    from apps.core.tasks import chat_async

    task = chat_async.delay(
        question=question,
        user_id=request.user.id,
        session_id=request.session.session_key or "anon",
    )

    return Response({
        "status": "processing",
        "task_id": task.id,
        "message": "Consulta en proceso. Consulta el estado en poll_url.",
        "poll_url": f"/api/v1/tasks/status/{task.id}/",
    }, status=202)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history_view(request):
    qs = LLMRequest.objects.filter(user=request.user).order_by('-created_at')[:50]
    return Response({'results': [{'prompt': e.prompt, 'response': e.response} for e in qs]})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def llm_chat_view(request):
    question = request.data.get('question', '').strip()
    if not question:
        question = request.data.get('message', '').strip()
    if not question:
        question = request.data.get('prompt', '').strip()
    if not question:
        return Response({'error': 'La pregunta no puede estar vacía.'}, status=400)

    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header and 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "user_id": str(request.user.id),
        "message": question,
    }

    try:
        # Llama al microservicio MS2 Chat
        response = requests.post(
            'http://ms2_chat:8002/api/v1/mole-ai/chat',
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        ai_response = data.get("respuesta", "Sin respuesta.")
        
        # Guardar en el historial de Django
        LLMRequest.objects.create(
            user=request.user,
            prompt=question,
            response=ai_response
        )
        
        return Response({
            "response": ai_response,
            "sources": data.get("sources", []),
            "disclaimer": data.get("disclaimer", "")
        })

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        try:
            err_detail = e.response.json()
        except Exception:
            err_detail = e.response.text
        logger.error(f"Error HTTP {status_code} desde MS2 Chat: {err_detail}")
        return Response({"error": "Error en motor de IA", "details": err_detail}, status=status_code)
    except requests.exceptions.RequestException as e:
        logger.error(f"Fallo de red al contactar MS2 Chat: {e}")
        return Response({"error": "No se pudo comunicar con el motor de IA.", "details": str(e)}, status=503)

# --- POLLING GENÉRICO DE TAREAS ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_status_view(request, task_id):
    """
    GET /api/v1/tasks/status/{task_id}/

    Unified polling endpoint for all async Celery operations.
    Returns the task state and result on completion.

    States:
      - PENDING:  Task received but not yet started
      - STARTED:  Worker picked up the task
      - SUCCESS:  Completed — result is in the response
      - FAILURE:  Failed — error info is in the response
      - RETRY:    Retrying after a transient failure
    """
    from celery.result import AsyncResult

    try:
        task = AsyncResult(task_id)
        state = task.state

        response_data = {
            "task_id": task_id,
            "state": state,
        }

        if state == "SUCCESS":
            response_data["result"] = task.result
        elif state == "FAILURE":
            response_data["error"] = str(task.result) if task.result else "Unknown error"
        elif state == "RETRY":
            response_data["info"] = str(task.info) if task.info else "Retrying..."

        return Response(response_data)

    except Exception as exc:
        return Response(
            {"error": "Task status fetch failed", "details": str(exc)},
            status=500,
        )


# --- SISTEMA E HISTORIAL ---
@api_view(['GET'])
def health_check_view(request):
    return Response({'status': 'healthy', 'timestamp': timezone.now().isoformat()})

@api_view(['GET'])
@permission_classes([AllowAny])
def fichas_public_view(request):
    return Response({"results": []})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def feedback_create_view(request):
    serializer = FeedbackTicketCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    v_data = cast(Dict[str, Any], serializer.validated_data)
    ticket = FeedbackTicket.objects.create(user=request.user, **v_data)
    return Response(FeedbackTicketResponseSerializer(ticket).data, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def consolidated_history_view(request):
    return Response({"history": []})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def plant_knowledge_view(request):
    return Response({"results": []})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sensor_log_view(request):
    return Response({"status": "created"}, status=201)