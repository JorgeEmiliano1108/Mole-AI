# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
import logging
import os
from typing import Any, cast

import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from rest_framework import authentication, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_models.models import LLMRequest
from apps.authentication.infrastructure.authentication import (
    HardwareAPIKeyAuthentication,
)

# Repositorios y Modelos
from .models import (
    AIDiagnostic,
    Device,
    DiagnosticoGeolocalizado,
    FeedbackTicket,
)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def revoke_device_token(request, id):
    """
    Revoca (desactiva) un dispositivo IoT.
    Soft‑delete: marca `is_active=False` sin borrar datos históricos.
    Solo el dueño o staff (igual que rotate_device_token).
    """
    try:
        device = Device.objects.get(pk=id)
    except Device.DoesNotExist:
        return Response(status=404)
    user = request.user
    if not (getattr(user, 'is_staff', False) or device.owner_id == getattr(user, 'id', None)):
        return Response({"error": "Sin permiso sobre este dispositivo."}, status=403)
    device.is_active = False
    device.save(update_fields=['is_active'])
    return Response(status=204)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rotate_device_token(request, id):
    """
    Rota el Bearer token de un dispositivo (RNF-02).
    Solo el dueño o staff. El token anterior queda invalidado de inmediato
    y el nuevo expira en 90 días (`auth_token_expires_at`).
    """
    try:
        device = Device.objects.get(pk=id)
    except Device.DoesNotExist:
        return Response(status=404)
    user = request.user
    if not (getattr(user, 'is_staff', False) or device.owner_id == getattr(user, 'id', None)):
        return Response({"error": "Sin permiso sobre este dispositivo."}, status=403)
    new_token = device.rotate_token()
    return Response({"auth_token": new_token, "expires_at": device.auth_token_expires_at}, status=200)

# Servicios y Serializers
from .serializers import (
    DiagnosticRequestSerializer,
    FeedbackTicketCreateSerializer,
    FeedbackTicketResponseSerializer,
    SensorBatchSerializer,
    SensorReadingSerializer,
)
from .services.safety_audit import log_safety_block
from .services.safety_validator import SafetyValidator
from .throttles import DiagnosticsThrottle, LLMChatThrottle, SensorDataThrottle

# Cliente MoleAI (RAG)
try:
    from apps.ai_models.services import MoleAIClient, MoleAIServiceError
except Exception:  # noqa: BLE001
    MoleAIClient = None
    MoleAIServiceError = Exception

logger = logging.getLogger(__name__)

# --- PERMISOS ---
class HardwareOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'is_hardware_device', False)

class DeviceBearerScheme(authentication.BaseAuthentication):
    """Declara el esquema `Bearer` sin validar (la validación vive en el permiso).

    DRF degrada AuthenticationFailed a 403 cuando ningún autenticador declara
    header `WWW-Authenticate`. Esta clase solo aporta `authenticate_header()`
    para que las denegaciones del permiso lleguen como 401. Nunca autentica.
    """

    def authenticate(self, request):
        return None

    def authenticate_header(self, request):
        return 'Bearer'


class DeviceBearerPermission(BasePermission):
    """Trama edge: Bearer por dispositivo (`Device.auth_token`), no llave global.

    La flota ESP32 envía `Authorization: Bearer <auth_token>` (firmware
    `transport_layer.c`), incompatible con `HardwareAPIKeyAuthentication`
    (header `X-Hardware-Api-Key` global). Este permiso resuelve el Device,
    exige `is_active` y token no expirado, y lo adjunta como `request.device`.
    Sin esto, `AllowAny` dejaba la ingesta abierta (REC-1 / S09).
    Deniega con 401 (AuthenticationFailed), no 403: el token es credencial.
    """
    message = 'Device not found or unauthorized'

    def has_permission(self, request, view):
        from django.utils import timezone
        from rest_framework import exceptions

        from .models import Device
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            raise exceptions.AuthenticationFailed(self.message)
        device = Device.objects.filter(auth_token=token, is_active=True).first()
        if not device:
            raise exceptions.AuthenticationFailed(self.message)
        expires_at = getattr(device, 'auth_token_expires_at', None)
        if expires_at and timezone.now() > expires_at:
            raise exceptions.AuthenticationFailed(self.message)
        request.device = device
        return True

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
    v_data = cast(dict[str, Any], serializer.validated_data)
    
    # [RF-IOTSEC-001] Protección Anti-Replay (ETSI EN 303 645)
    recorded_at = v_data.get('recorded_at')
    if recorded_at:
        delta_seconds = abs((timezone.now() - recorded_at).total_seconds())
        if delta_seconds > 300:
            logger.warning(f"Bloqueo Anti-Replay: Delta de {delta_seconds}s detectado en ESP32.")
            return Response({"error": "Replay attack protection: Timestamp out of sync (> 300s)"}, status=403)

    
    from apps.core.services.legacy_ingest import (
        PlantNotBoundError,
        ingest_legacy_reading,
    )

    try:
        ingest_legacy_reading(v_data)
        return Response({"status": "success", "registered": 1}, status=201)
    except PlantNotBoundError:
        return Response(
            {"error": "plant_id no vinculado a ningún dispositivo"}, status=404
        )
    except Exception:
        logger.exception("sensor_ingest_failed")
        return Response(
            {"error": "No se pudo procesar la lectura."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@authentication_classes([HardwareAPIKeyAuthentication])
@permission_classes([HardwareOnlyPermission])
@throttle_classes([SensorDataThrottle])
def sensor_batch_view(request):
    serializer = SensorBatchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    v_data = cast(dict[str, Any], serializer.validated_data)
    batch = cast(list[dict[str, Any]], v_data['batch'])
    
    # [RF-IOTSEC-001] Protección Anti-Replay para Lotes
    if batch and 'recorded_at' in batch[0]:
        delta_seconds = abs((timezone.now() - batch[0]['recorded_at']).total_seconds())
        if delta_seconds > 300:
            logger.warning(f"Bloqueo Anti-Replay en Lote: Delta de {delta_seconds}s detectado.")
            return Response({"error": "Replay attack protection in batch: Timestamp out of sync (> 300s)"}, status=403)

    
    from apps.core.services.legacy_ingest import ingest_legacy_batch

    # A3 FREEZE: sensor_logs es archivo de solo lectura; el lote se
    # demultiplexa a AmbientReading + SoilReading (ítems sin binding se omiten).
    result = ingest_legacy_batch(batch)
    payload: dict[str, Any] = {
        "status": "success",
        "registered": result["accepted"],
    }
    if result["skipped"]:
        payload["skipped_unbound_plants"] = result["skipped"]
    return Response(payload, status=201)

@api_view(['PATCH'])
@authentication_classes([HardwareAPIKeyAuthentication])
@permission_classes([HardwareOnlyPermission])
@throttle_classes([SensorDataThrottle])
def sensor_data_patch_view(request, pk):
    # A3 FREEZE: sensor_logs es archivo de solo lectura (410 Gone). La
    # inyección de pH post-inferencia debe dirigirse a SoilReading mediante
    # un endpoint dedicado (pendiente de diseño).
    return Response(
        {
            "error": "Endpoint obsoleto (410 Gone). La tabla sensor_logs es "
            "archivo de solo lectura; usa el esquema AmbientReading/SoilReading."
        },
        status=410,
    )

class EdgeNodeIngestView(APIView):
    """
    POST /api/v1/sensor-data/edge-batch/
    Ingests the compact ESP32 telemetry frame and demultiplexes into
    AmbientReading + SoilReading (1:N relational schema).

    Decisions: A1=partial success, A2=ACID, A3=freeze SensorLog, A4=future-only anti-replay.
    Auth: DeviceBearerPermission (Bearer por dispositivo + expiración).
    DeviceBearerScheme declara el esquema para que las denegaciones sean 401.
    """
    authentication_classes = (DeviceBearerScheme,)
    permission_classes = (DeviceBearerPermission,)
    throttle_classes = (SensorDataThrottle,)

    def post(self, request):
        from apps.core.services.edge_ingest import ingest_frame

        from .serializers import EdgeFrameSerializer

        # ── Auth: Device resuelto por DeviceBearerPermission ───────────────
        device = getattr(request, 'device', None)
        if device is None:  # Defensa en profundidad si el permiso se retira
            from .models import Device as DeviceModel
            auth_header = request.headers.get('Authorization', '').replace('Bearer ', '')
            device = DeviceModel.objects.filter(auth_token=auth_header).first()
        if not device or not getattr(device, 'is_active', True):
            return Response({"error": "Device not found or unauthorized"}, status=401)

        # ── Validate compact contract ───────────────────────────────────
        serializer = EdgeFrameSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "Invalid frame", "details": serializer.errors}, status=400)

        # Lógica compartida (apps/core/services/edge_ingest.py): idéntica
        # respuesta que antes del refactor (ingesta directa, sin dedupe).
        result = ingest_frame(device, serializer.validated_data)

        return Response({
            "status": "ingested",
            "ambient": result["ambient"],
            "soil_mapped": result["soil_mapped"],
            "orphaned_pins": result["orphaned_pins"],
        })


class SyncBatchView(APIView):
    """
    POST /api/v1/sync/batch/ — Sincronización edge con cursor (MRF03/RNF06).

    JSON-RPC 2.0 estricto sobre el mismo auth DeviceBearer que `edge-batch/`
    (dual-stack: la forma legacy sigue viva sin cambios).
    Request: {"jsonrpc":"2.0","method":"sync.telemetry",
              "params":{"cursor":<iso|null>,"frames":[{ts,ri,a,s}...]},"id":any}
    Response: {"jsonrpc":"2.0",
               "result":{"applied_up_to":<iso|null>,"accepted":[i...],
                         "conflicts":[{index,error,details?}...]},"id":same}
    Errores protocolo: {"jsonrpc":"2.0","error":{"code","message"},"id":same|null}
    Códigos: -32700 parse, -32600 request inválido, -32601 método desconocido,
             -32602 parámetros inválidos. Auth (401) y throttle igual que edge-batch.
    Semántica: éxito parcial por trama (A1); cada trama en su transacción (A2);
    reenvíos idempotentes (`dedupe=True`); conflictos = tramas rechazadas con
    motivo (server-wins documentado: lo aceptado manda).
    """

    authentication_classes = (DeviceBearerScheme,)
    permission_classes = (DeviceBearerPermission,)
    throttle_classes = (SensorDataThrottle,)

    METHOD = "sync.telemetry"

    def post(self, request):
        from apps.core.services.edge_ingest import ingest_frame

        from .serializers import EdgeFrameSerializer

        device = getattr(request, 'device', None)
        if device is None:
            from .models import Device as DeviceModel
            auth_header = request.headers.get('Authorization', '').replace('Bearer ', '')
            device = DeviceModel.objects.filter(auth_token=auth_header).first()
        if not device or not getattr(device, 'is_active', True):
            return Response({"error": "Device not found or unauthorized"}, status=401)

        body = request.data
        rpc_id = body.get("id") if isinstance(body, dict) else None
        if not isinstance(body, dict):
            return self._err(-32700, "Parse error: se esperaba objeto JSON", rpc_id)
        if body.get("jsonrpc") != "2.0" or "method" not in body:
            return self._err(-32600, "Invalid Request: jsonrpc=='2.0' y method requeridos", rpc_id)
        if body.get("method") != self.METHOD:
            return self._err(-32601, f"Method not found: {body.get('method')}", rpc_id)
        params = body.get("params", {})
        if not isinstance(params, dict) or not isinstance(params.get("frames"), list):
            return self._err(-32602, "Invalid params: params.frames (lista) requerido", rpc_id)

        accepted = []
        conflicts = []
        applied_up_to = params.get("cursor")
        for i, raw in enumerate(params["frames"]):
            if not isinstance(raw, dict):
                conflicts.append({"index": i, "error": "frame no es objeto"})
                continue
            serializer = EdgeFrameSerializer(data=raw)
            if not serializer.is_valid():
                conflicts.append({
                    "index": i, "error": "Invalid frame",
                    "details": serializer.errors,
                })
                continue
            try:
                result = ingest_frame(
                    device, serializer.validated_data, dedupe=True
                )
            except Exception:
                logger.exception("SyncBatch: fallo trama %d device=%s", i, device.pk)
                conflicts.append({"index": i, "error": "Error procesando trama"})
                continue
            accepted.append(i)
            applied_up_to = result["recorded_at"].isoformat()

        return Response({
            "jsonrpc": "2.0",
            "result": {
                "applied_up_to": applied_up_to,
                "accepted": accepted,
                "conflicts": conflicts,
            },
            "id": rpc_id,
        })

    @staticmethod
    def _err(code, message, rpc_id):
        return Response({
            "jsonrpc": "2.0",
            "error": {"code": code, "message": message},
            "id": rpc_id,
        })

# --- INTELIGENCIA ARTIFICIAL Y DIAGNÓSTICOS ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([DiagnosticsThrottle])
def diagnostic_view(request):
    """
    POST /api/v1/diagnostics/
    Envía imagen a MS1 de forma asíncrona via Celery.
    No bloquea el request - el frontend hace polling del task_id.
    """
    from apps.authentication.consent import require_ai_consent
    if not require_ai_consent(request.user):
        return Response(
            {"error": "Se requiere consentimiento de IA.",
             "code": "CONSENT_REQUIRED"},
            status=status.HTTP_403_FORBIDDEN,
        )
    from utils.uploads import safe_temp_path

    from apps.ai_models.tasks import analyze_vision_async

    serializer = DiagnosticRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    v_data = serializer.validated_data

    image_file = v_data.get('image')
    if not image_file:
        return Response({"error": "Imagen requerida"}, status=400)

    # Helper canónico anti path-traversal (Guardrail B).
    temp_path = safe_temp_path(
        image_file.name, prefix=f"diagnostic_{request.user.id}_"
    )
    
    with open(temp_path, 'wb+') as f:
        f.writelines(image_file.chunks())
    
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


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def diagnostic_patch_pvu_reason_view(request, id):
    """PATCH /api/v1/diagnostics/<id>/ — actualiza pvu_reason post-ruta.

    El SafetyValidator intercepta motivos inseguros antes de persistirlos
    (fail-closed). Silent-compliance: sin menciones normativas en respuestas.
    """
    reason = request.data.get('pvu_reason')
    if reason is None:
        return Response({"error": "pvu_reason requerido."}, status=status.HTTP_400_BAD_REQUEST)
    reason_text = str(reason)[:30]
    safety = SafetyValidator().validate({"pvu_reason": reason_text})
    if not safety.safe:
        from apps.core.services.safety_presentation import public_safety_error
        return Response(
            public_safety_error(source="diagnostics"),
            status=safety.status_code,
        )
    updated = AIDiagnostic.objects.filter(id=id, user=request.user).update(
        pvu_reason=reason_text
    )
    if updated == 0:
        return Response({"error": "Diagnóstico no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    return Response({"status": "updated"})


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
    except requests.exceptions.RequestException:
        logger.exception("weather_proxy_failed")
        return Response(
            {'error': 'No se pudo obtener la información del clima.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

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

def _call_ms2_chat_sync(user_id: str, question: str, session_id: str | None = None, auth_header: str = "") -> dict[str, Any]:
    """Llama al microservicio de chat vía MCP o REST según settings.MCP_ENABLED.

    Si MCP está habilitado y falla, cae al camino REST para no dejar al usuario
    sin respuesta.
    """
    if settings.MCP_ENABLED:
        try:
            from apps.ai_models.infrastructure.mcp_client import MCPChatClient
            return MCPChatClient().chat(
                user_id=user_id,
                message=question,
                session_id=session_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("MCP chat failed, falling back to REST: %s", exc)

    # REST fallback (anterior).
    headers = {"Authorization": auth_header, "Content-Type": "application/json"}
    payload = {"user_id": user_id, "message": question}
    response = requests.post(
        f"{settings.MOLE_AI_SERVICE_URL}/api/v1/mole-ai/chat",
        json=payload,
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([LLMChatThrottle])
def llm_chat_view(request):
    from apps.authentication.consent import require_ai_consent
    if not require_ai_consent(request.user):
        return Response(
            {"error": "Se requiere consentimiento de IA.",
             "code": "CONSENT_REQUIRED"},
            status=status.HTTP_403_FORBIDDEN,
        )
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

    try:
        # MCP o REST hacia MS2 Chat
        data = _call_ms2_chat_sync(
            user_id=str(request.user.id),
            question=question,
            session_id=request.session.session_key,
            auth_header=auth_header,
        )
        ai_response = data.get("respuesta") or "Sin respuesta."

        # Gate de seguridad fail-closed: el SafetyValidator vive en el host Django
        # y actúa como middleware de salida hacia el dispositivo móvil.
        safety = SafetyValidator().validate({"text": ai_response})
        if not safety.safe:
            log_safety_block(
                user_id=request.user.id,
                safety_result=safety,
                task_id=None,
                source="chat",
            )
            from apps.core.services.safety_presentation import public_safety_error
            # Silent-compliance: el motivo/código reales quedan en AuditLog;
            # al usuario solo mensaje genérico (sin menciones normativas).
            return Response(
                public_safety_error(source="chat"),
                status=status.HTTP_403_FORBIDDEN,
            )

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
        except Exception:  # noqa: BLE001
            err_detail = e.response.text
        logger.error("Error HTTP %s desde MS2 Chat: %s", status_code, err_detail)
        return Response({"error": "Error en motor de IA", "details": err_detail}, status=status_code)
    except requests.exceptions.RequestException:
        logger.exception("chat_network_failed")
        return Response(
            {"error": "No se pudo comunicar con el motor de IA."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except Exception:
        logger.exception("chat_unexpected_failed")
        return Response(
            {"error": "Error en motor de IA."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

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

    except Exception:
        logger.exception("task_status_fetch_failed")
        return Response(
            {"error": "No se pudo consultar el estado de la tarea."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# --- SISTEMA E HISTORIAL ---
@api_view(['GET'])
@permission_classes([AllowAny])  # Health-check público (contrato móvil §7: ping pre-login).
# Solo expone {status, timestamp}; sin PII ni estado interno.
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
    v_data = cast(dict[str, Any], serializer.validated_data)
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


# --- DOMINIO LEGAL / SAFETY GATE ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def safety_validate_view(request):
    """POST /api/v1/safety/validate/ — Gate de dominio legal.

    Valida texto o prescripción de agroquímico contra los contratos
    docs/safety/*.json y safety_rules.yaml. Devuelve 403 cuando el
    SafetyValidator detecta una violación (fail-closed).
    """
    from apps.core.services.safety_presentation import (
        PUBLIC_BLOCK_CODE,
        PUBLIC_BLOCK_MESSAGE,
    )

    payload = request.data or {}
    safety = SafetyValidator().validate(payload)
    if safety.safe:
        return Response({"safe": True, "code": safety.code})
    # Silent-compliance: sin menciones normativas en la respuesta.
    return Response(
        {"safe": False, "code": PUBLIC_BLOCK_CODE, "reason": PUBLIC_BLOCK_MESSAGE},
        status=safety.status_code,
    )
