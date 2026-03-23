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
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import random
from apps.core.infrastructure.repositories.models import SensorLog
from apps.plants.infrastructure.repositories.models import UserPlant
from django.shortcuts import get_object_or_404

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def telemetry_latest_view(request):
    """
    GET /api/v1/telemetry/latest/?plant_id=<uuid>
    Returns the most recent SensorLog for the given plant_id if the plant belongs to the request.user.
    """
    plant_id = request.GET.get('plant_id')
    if not plant_id:
        return Response({'error': 'plant_id query parameter is required.'}, status=400)

    # Verify ownership: plant must belong to the authenticated user
    try:
        plant = UserPlant.objects.get(id=plant_id, user=request.user)
    except UserPlant.DoesNotExist:
        return Response({'error': 'Plant not found or does not belong to the user.'}, status=404)

    log = SensorLog.objects.filter(plant_id=plant_id).order_by('-recorded_at').first()
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