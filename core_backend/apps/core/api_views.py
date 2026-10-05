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

from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.authentication.infrastructure.local_jwt_auth import LocalJWTAuthentication
from apps.core.serializers import SensorReadingSerializer
from apps.plants.models import UserPlant

logger = logging.getLogger(__name__)


# ── Mock data (legacy, dev-only, gone in production) ───────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def mock_sensor_data(request):
    return JsonResponse(
        {"detail": "Endpoint de datos simulados retirado."},
        status=410,
    )


# ── Telemetry — Async (Sprint 4) ────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def telemetry_latest_view(request):
    """
    GET /api/v1/telemetry/latest/?plant_id=<uuid>
    Returns the most recent SensorLog for the given plant_id if the plant belongs to the request.user.
    Nota: vista síncrona a propósito — el DRF instalado no soporta vistas
    async (un `async def` aquí devolvía la corrutina sin ejecutar).
    """
    plant_id = request.GET.get('plant_id')
    if not plant_id:
        return Response({'error': 'plant_id query parameter is required.'}, status=400)

    # Verify ownership: plant must belong to the authenticated user
    try:
        UserPlant.objects.get(id=plant_id, user=request.user)
    except UserPlant.DoesNotExist:
        return Response({'error': 'Plant not found or does not belong to the user.'}, status=404)

    from apps.core.models import HardwareBinding

    # A3 FREEZE: se lee del esquema 1:N canónico, no del archivo SensorLog.
    binding = (
        HardwareBinding.objects.select_related("device")
        .filter(plant_id=plant_id)
        .first()
    )
    if binding is None:
        return Response({'error': 'No telemetry available for this plant.'}, status=404)

    from apps.core.models import AmbientReading, SoilReading

    soil = SoilReading.objects.filter(binding=binding).order_by('-recorded_at').first()
    ambient = AmbientReading.objects.filter(device=binding.device).order_by('-recorded_at').first()

    if not soil and not ambient:
        return Response({'error': 'No telemetry available for this plant.'}, status=404)

    latest_at = None
    for reading in (soil, ambient):
        if reading is not None and (latest_at is None or reading.recorded_at > latest_at):
            latest_at = reading.recorded_at

    payload = {
        'plant_id': str(plant_id),
        'recorded_at': latest_at.isoformat() if latest_at else None,
        'soil_humidity': soil.soil_humidity if soil else None,
        'air_humidity': ambient.air_humidity if ambient else None,
        'air_temperature': ambient.air_temperature if ambient else None,
        'uv_index': ambient.uv_index if ambient else None,
        'ph_level': soil.ph_level if soil else None,
    }
    return Response(payload)


# ── IoT Ingest — JWT-Protected (Sprint 2, Zero-Trust) ───────────────────────

@api_view(['POST'])
@authentication_classes([LocalJWTAuthentication])
@permission_classes([IsAuthenticated])
def sensors_ingest_view(request):
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

    if not serializer.is_valid():
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

    from apps.core.services.legacy_ingest import (
        PlantNotBoundError,
        ingest_legacy_reading,
    )

    try:
        # A3 FREEZE: sensor_logs es archivo de solo lectura; se escribe al
        # esquema 1:N (AmbientReading + SoilReading vía HardwareBinding).
        ingest_legacy_reading(v_data)
        return Response({"status": "success", "registered": 1}, status=201)
    except PlantNotBoundError:
        return Response({"error": "plant_id not registered"}, status=404)
    except Exception:
        logger.exception("Sensor ingest failed")
        return Response(
            {"error": "No se pudo procesar la lectura."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ── Heartbeat Liveness (Sprint Dashboard UI — ISSUE-03 / INGEST-04) ─────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def device_health_view(request, id):
    """
    GET /api/v1/devices/{id}/health/
    Reads from AmbientReading + SoilReading (1:N schema). SensorLog is frozen.

    Query budget: constant 4 queries (Device, Ambient, Bindings+Subquery, SoilReadings IN).
    """
    from django.db.models import OuterRef, Subquery
    from django.utils import timezone

    from apps.core.models import AmbientReading, Device, HardwareBinding, SoilReading

    try:
        device = Device.objects.get(id=id)
    except Device.DoesNotExist:
        return Response({'error': 'Device not found.'}, status=404)

    # S2 BOLA: solo el dueño o staff; 404 para no oracular existencia.
    if device.owner_id != request.user.id and not (
            request.user.is_staff or request.user.is_superuser):
        return Response({'error': 'Device not found.'}, status=404)

    now = timezone.now()
    delta_seconds = 0
    if device.last_seen:
        delta_seconds = int((now - device.last_seen).total_seconds())

    # SRE Metrics (mocks -- pending historical tables)
    sre_metrics = {
        "uptime_pct_24h": 99.8,
        "ws_reconnects_24h": 2,
        "report_interval_minutes": device.report_interval_minutes,
    }

    # Q1: Latest ambient reading (1 query)
    ambient = AmbientReading.objects.filter(device=device).order_by('-recorded_at').first()
    ambient_data = None
    if ambient:
        ambient_data = {
            "air_temperature": ambient.air_temperature,
            "air_humidity": ambient.air_humidity,
            "uv_index": ambient.uv_index,
            "light_level": ambient.light_level,
            "recorded_at": ambient.recorded_at.isoformat(),
        }

    # Q2: Bindings annotated with latest SoilReading PK via Subquery (1 query)
    latest_soil_subquery = (
        SoilReading.objects
        .filter(binding=OuterRef('pk'))
        .order_by('-recorded_at')
        .values('pk')[:1]
    )
    bindings = (
        HardwareBinding.objects
        .filter(device=device)
        .select_related('plant', 'plant__species')
        .annotate(latest_soil_id=Subquery(latest_soil_subquery))
    )

    # Q3: Batch-fetch all latest soil readings in a single IN() (1 query)
    soil_ids = [b.latest_soil_id for b in bindings if b.latest_soil_id is not None]
    latest_readings_by_binding = {}
    if soil_ids:
        latest_readings_by_binding = {
            r.binding_id: r
            for r in SoilReading.objects.filter(pk__in=soil_ids)
        }

    # Assembly (zero additional queries)
    soil_readings = []
    for binding in bindings:
        reading = latest_readings_by_binding.get(binding.pk)
        entry = {
            "pin": binding.hardware_pin,
            "plant_id": str(binding.plant_id),
            "plant_nickname": binding.plant.nickname if binding.plant else None,
            "soil_humidity": reading.soil_humidity if reading else None,
            "recorded_at": reading.recorded_at.isoformat() if reading else None,
        }
        species = getattr(binding.plant, 'species', None) if binding.plant else None
        if species:
            entry["species"] = species.scientific_name
            entry["ideal_humidity_min"] = getattr(species, 'ideal_humidity_min', None)
            entry["ideal_humidity_max"] = getattr(species, 'ideal_humidity_max', None)
            entry["ideal_ph_min"] = getattr(species, 'ideal_ph_min', None)
            entry["ideal_ph_max"] = getattr(species, 'ideal_ph_max', None)
        soil_readings.append(entry)

    payload = {
        "device_id": str(device.id),
        "device_name": device.name,
        "status": device.status,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "last_seen_delta_seconds": delta_seconds,
        "ambient": ambient_data,
        "soil": soil_readings,
        "sre_metrics": sre_metrics,
    }

    return Response(payload)


# -- FE-03: HardwareBinding CRUD endpoints --------------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def device_bindings_view(request, id):
    """
    GET  /api/v1/devices/{id}/bindings/  -- list all bindings for device
    POST /api/v1/devices/{id}/bindings/  -- create a new binding
    """
    from apps.core.models import Device, HardwareBinding
    from apps.plants.models import UserPlant

    try:
        device = Device.objects.get(id=id)
    except Device.DoesNotExist:
        return Response({'error': 'Device not found.'}, status=404)

    # S2 BOLA: lectura de bindings solo dueño o staff (el POST/DELETE ya
    # exigen staff vía SRE; el GET filtraba por dispositivo sin dueño).
    if device.owner_id != request.user.id and not (
            request.user.is_staff or request.user.is_superuser):
        return Response({'error': 'Device not found.'}, status=404)

    if request.method == 'GET':
        bindings = (
            HardwareBinding.objects
            .filter(device=device)
            .select_related('plant', 'plant__species')
        )
        data = []
        for b in bindings:
            entry = {
                'id': b.pk,
                'hardware_pin': b.hardware_pin,
                'plant_id': str(b.plant_id),
                'plant_nickname': b.plant.nickname if b.plant else None,
                'species': b.plant.species.scientific_name if b.plant and b.plant.species else None,
            }
            data.append(entry)
        return Response({'bindings': data, 'count': len(data)})

    # POST (PATCH-03: RBAC SRE only)
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({'error': 'SRE role required to mutate bindings.'}, status=403)

    pin = request.data.get('hardware_pin', '').strip()
    plant_id = request.data.get('plant_id', '').strip()

    if not pin or not plant_id:
        return Response({'error': 'hardware_pin and plant_id are required.'}, status=400)

    try:
        plant = UserPlant.objects.get(id=plant_id)
    except UserPlant.DoesNotExist:
        return Response({'error': 'Plant not found.'}, status=404)

    if HardwareBinding.objects.filter(device=device, hardware_pin=pin).exists():
        return Response({'error': f'Pin {pin} is already bound on this device.'}, status=409)

    if HardwareBinding.objects.filter(plant=plant).exists():
        return Response({'error': 'This plant is already bound to a pin.'}, status=409)

    binding = HardwareBinding.objects.create(device=device, hardware_pin=pin, plant=plant)
    return Response({
        'status': 'created',
        'id': binding.pk,
        'hardware_pin': binding.hardware_pin,
        'plant_id': str(binding.plant_id),
    }, status=201)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def device_binding_delete_view(request, id, binding_id):
    """
    DELETE /api/v1/devices/{id}/bindings/{binding_id}/
    """
    # PATCH-03: RBAC SRE only
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({'error': 'SRE role required to delete bindings.'}, status=403)

    from apps.core.models import Device, HardwareBinding

    try:
        device = Device.objects.get(id=id)
    except Device.DoesNotExist:
        return Response({'error': 'Device not found.'}, status=404)

    try:
        binding = HardwareBinding.objects.get(pk=binding_id, device=device)
    except HardwareBinding.DoesNotExist:
        return Response({'error': 'Binding not found.'}, status=404)

    binding.delete()
    return Response(status=204)