# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
import json
import os
import math
import logging
import random
import uuid
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
    DiagnosticoGeolocalizado, FeedbackTicket
)
from apps.plants.models import UserPlant
from apps.ai_models.models import LLMRequest
from apps.authentication.infrastructure.authentication import HardwareAPIKeyAuthentication

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
    
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"diagnostic_{request.user.id}_{image_file.name}")
    
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
    diagnostics = AIDiagnostic.objects.filter(user=request.user).order_by('-analyzed_at')[:limit]
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
    try:
        from apps.core.services.pdf_generator import generate_diagnostic_pdf
        pdf_bytes = generate_diagnostic_pdf(id)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="diagnostico_{id}.pdf"'
        return response
    except Exception as e:
        return Response({"error": str(e)}, status=500)

# --- MAPAS Y HOTSPOTS ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def map_hotspots_view(request):
    qs = DiagnosticoGeolocalizado.objects.all()[:100]
    results = [{'lat': r.latitude, 'lng': r.longitude, 'severity': r.severity} for r in qs]
    return Response({'hotspots': results})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def diagnosticos_geolocalizados_list(request):
    qs = DiagnosticoGeolocalizado.objects.filter(user=request.user)[:50]
    return Response({'results': [{'id': r.id, 'condition': r.condition_name} for r in qs]})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def diagnosticos_geolocalizados_create(request):
    return Response({"status": "created"}, status=201)

# --- CHAT Y RAG ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([LLMChatThrottle])
def chat_fallback_view(request):
    if MoleAIClient is None:
        return Response({'error': 'AI client not available'}, status=500)
    try:
        question = cast(str, request.data.get('question', '')).strip()
        client = MoleAIClient()
        result = async_to_sync(client.generate_chat_response)(
            query=question,
            user_id=request.user.id,
            session_id=request.session.session_key or "anon"
        )
        return Response({"answer": result.get('answer'), "disclaimer": result.get('disclaimer')})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history_view(request):
    qs = LLMRequest.objects.filter(user=request.user).order_by('-created_at')[:50]
    return Response({'results': [{'prompt': e.prompt, 'response': e.response} for e in qs]})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def llm_chat_view(request):
    return Response({"response": "Chat básico activo"})

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