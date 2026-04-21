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
Lightweight API views for core telemetry and IoT ingest endpoints.

Sprint 2: sensors_ingest_view — JWT-protected IoT ingest (Zero-Trust)
Sprint 4: async def views — non-blocking I/O via ASGI
"""
import logging
import random

from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.authentication.infrastructure.authentication import SupabaseAuthentication
from apps.core.models import SensorLog
from apps.core.serializers import SensorReadingSerializer
from apps.plants.models import UserPlant

logger = logging.getLogger(__name__)


# ── Mock data (legacy, AllowAny — kept for backward compatibility) ───────────

@api_view(['GET'])
@permission_classes([AllowAny])
def mock_sensor_data(request):
    return JsonResponse({
        "temperature": round(random.uniform(20.0, 30.0), 1),
        "humidity": random.randint(40, 60),
        "soil_ph": round(random.uniform(6.0, 7.5), 1),
        "uv_index": random.randint(1, 5),
        "health_status": "OPTIMAL",
        "irrigation_active": False,
        "lights_active": True
    })


# ── Telemetry — Async (Sprint 4) ────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def telemetry_latest_view(request):
    """
    GET /api/v1/telemetry/latest/?plant_id=<uuid>
    Returns the most recent SensorLog for the given plant_id if the plant belongs to the request.user.
    """
    plant_id = request.GET.get('plant_id')
    if not plant_id:
        return Response({'error': 'plant_id query parameter is required.'}, status=400)

    # Verify ownership: plant must belong to the authenticated user
    try:
        await sync_to_async(
            UserPlant.objects.get, thread_sensitive=True
        )(id=plant_id, user=request.user)
    except UserPlant.DoesNotExist:
        return Response({'error': 'Plant not found or does not belong to the user.'}, status=404)

    log = await sync_to_async(
        lambda: SensorLog.objects.filter(plant_id=plant_id)
                .order_by('-recorded_at')
                .first(),
        thread_sensitive=True,
    )()

    if not log:
        return Response({'error': 'No telemetry available for this plant.'}, status=404)

    payload = {
        'plant_id': str(plant_id),
        'recorded_at': log.recorded_at.isoformat(),
        'soil_humidity': log.soil_humidity,
        'air_humidity': log.air_humidity,
        'air_temperature': log.air_temperature,
        'uv_index': log.uv_index,
        'ph_level': log.ph_level,
    }
    return Response(payload)


# ── IoT Ingest — JWT-Protected (Sprint 2, Zero-Trust) ───────────────────────

@api_view(['POST'])
@authentication_classes([SupabaseAuthentication])
@permission_classes([IsAuthenticated])
async def sensors_ingest_view(request):
    """
    POST /api/v1/sensors/ingest
    JWT-protected endpoint for IoT sensor data ingestion.

    This replaces the legacy HardwareAPIKey-based sensor_data_view for
    nodes that have been upgraded to M2M JWT authentication (Zero-Trust).
    The JwtHttpMiddleware in the middleware stack has already validated
    the Bearer token before this view executes.

    Payload: same schema as SensorReadingSerializer.
    """
    serializer = SensorReadingSerializer(data=request.data)

    is_valid = await sync_to_async(
        serializer.is_valid, thread_sensitive=True
    )()
    if not is_valid:
        return Response(
            {"error": "Invalid payload", "details": serializer.errors},
            status=400,
        )

    v_data = serializer.validated_data

    # Anti-Replay protection (ETSI EN 303 645)
    recorded_at = v_data.get("recorded_at")
    if recorded_at:
        delta_seconds = abs((timezone.now() - recorded_at).total_seconds())
        if delta_seconds > 300:
            logger.warning(
                "Anti-Replay block on ingest: delta=%ss uid=%s",
                delta_seconds,
                getattr(request, "supabase_uid", "unknown"),
            )
            return Response(
                {"error": "Replay attack protection: Timestamp out of sync (> 300s)"},
                status=403,
            )

    plant_exists = await sync_to_async(
        lambda: UserPlant.objects.filter(id=v_data["plant_id"]).exists(),
        thread_sensitive=True,
    )()
    if not plant_exists:
        return Response({"error": "plant_id not registered"}, status=404)

    try:
        await sync_to_async(
            lambda: SensorLog.objects.create(
                plant_id=v_data["plant_id"],
                recorded_at=v_data.get("recorded_at"),
                soil_humidity=v_data.get("soil_humidity"),
                air_temperature=v_data.get("air_temperature"),
                uv_index=v_data.get("uv_index"),
                light_level=v_data.get("light_level"),
                ph_level=v_data.get("ph_level"),
            ),
            thread_sensitive=True,
        )()
        return Response({"status": "success", "registered": 1}, status=201)
    except Exception as exc:
        logger.exception("Sensor ingest failed: %s", exc)
        return Response({"error": str(exc)}, status=500)