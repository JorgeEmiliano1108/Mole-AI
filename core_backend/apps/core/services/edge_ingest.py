"""Ingesta edge compartida (MRF03, ADR-0002): UNA implementación.

Tanto `EdgeNodeIngestView` (REST `edge-batch/`, trama única) como `SyncBatchView`
(JSON-RPC `sync/batch`, lote con cursor) demultiplexan vía :func:`ingest_frame`:
heartbeat + `AmbientReading` + `SoilReading` en una transacción ACID por trama
(A1 éxito parcial entre tramas, A2 atomicidad por trama).
"""
import logging
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.core.models import (
    AmbientReading,
    Device,
    HardwareBinding,
    SoilReading,
)

logger = logging.getLogger(__name__)


def ingest_frame(device, validated, *, dedupe=False):
    """Ingiere UNA trama validada (`EdgeFrameSerializer.validated_data`).

    Retorna dict `{recorded_at, ambient: bool, soil_mapped: int,
    orphaned_pins: [str]}`. Lanza excepción si la DB falla (el llamador
    decide atomicidad del lote).

    `dedupe=True` (solo vía `sync/batch`): salta lecturas ya presentes para
    el mismo `(device|binding, recorded_at)` — reenvíos idempotentes tras
    fallo ambiguo. El path legacy `edge-batch/` conserva inserción directa
    (sin cambio de comportamiento).
    """
    recorded_at = datetime.fromtimestamp(validated['ts'], tz=timezone.utc)
    ambient_data = validated.get('a')
    soil_items = validated.get('s', [])

    soil_mapped = 0
    orphaned_pins = []

    with transaction.atomic():
        update_fields = {'last_seen': timezone.now(), 'status': 'online'}
        if validated.get('ri'):
            update_fields['report_interval_minutes'] = validated['ri']
        Device.objects.filter(pk=device.pk).update(**update_fields)

        ambient_done = False
        if ambient_data:
            if not dedupe or not AmbientReading.objects.filter(
                device=device, recorded_at=recorded_at
            ).exists():
                AmbientReading.objects.create(
                    device=device,
                    recorded_at=recorded_at,
                    **ambient_data
                )
            ambient_done = True

        if soil_items:
            bindings_by_pin = {
                b.hardware_pin: b
                for b in HardwareBinding.objects.filter(device=device)
            }
            soil_objects = []
            for item in soil_items:
                binding = bindings_by_pin.get(str(item['p']))
                if binding:
                    if dedupe and SoilReading.objects.filter(
                        binding=binding, recorded_at=recorded_at
                    ).exists():
                        soil_mapped += 1  # Ya aplicada: cuenta como éxito.
                        continue
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
                soil_mapped += len(soil_objects)

            if orphaned_pins:
                logger.warning(
                    "EdgeIngest: device=%s orphaned pins: %s",
                    device.pk, orphaned_pins
                )

    return {
        "recorded_at": recorded_at,
        "ambient": ambient_done,
        "soil_mapped": soil_mapped,
        "orphaned_pins": orphaned_pins,
    }
