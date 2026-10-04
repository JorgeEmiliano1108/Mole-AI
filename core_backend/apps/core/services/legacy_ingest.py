"""Redirección de ingesta legacy (wide-table) al esquema 1:N canónico.

Los endpoints `sensor-data/`, `sensor-data/batch/`, `sensors/ingest` y el
daemon MQTT reciben payloads centrados en `plant_id` (formato SensorLog).
La tabla `sensor_logs` está congelada (A3 FREEZE, solo archivo de lectura):
toda escritura nueva debe ir a `AmbientReading` + `SoilReading`.

Resolución de identidad: la llave de hardware global no identifica dispositivo;
el dispositivo se resuelve vía `HardwareBinding(plant)`. Una planta sin
binding no puede atribuir telemetría → `PlantNotBoundError` (el llamador
responde 404).
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.core.models import AmbientReading, Device, HardwareBinding, SoilReading

AMBIENT_FIELDS = ("air_temperature", "air_humidity", "light_level", "uv_index")


class PlantNotBoundError(Exception):
    """La planta no está vinculada a ningún dispositivo vía HardwareBinding."""


def ingest_legacy_reading(validated: dict) -> dict[str, bool]:
    """Persiste un payload wide-table en el esquema 1:N.

    Retorna `{"ambient": bool, "soil": bool}` según qué filas se crearon.
    Lanza `PlantNotBoundError` si la planta no tiene binding.
    """
    binding = (
        HardwareBinding.objects.select_related("device")
        .filter(plant_id=validated["plant_id"])
        .first()
    )
    if binding is None:
        raise PlantNotBoundError(
            f"plant_id {validated['plant_id']} sin HardwareBinding; "
            f"vincula la planta a un dispositivo antes de ingestion."
        )
    device = binding.device
    recorded_at = validated.get("recorded_at") or timezone.now()

    created = {"ambient": False, "soil": False}
    with transaction.atomic():
        ambient_data = {
            field: validated.get(field)
            for field in AMBIENT_FIELDS
            if validated.get(field) is not None
        }
        if ambient_data:
            AmbientReading.objects.create(
                device=device, recorded_at=recorded_at, **ambient_data
            )
            created["ambient"] = True
        if validated.get("soil_humidity") is not None:
            SoilReading.objects.create(
                binding=binding,
                recorded_at=recorded_at,
                soil_humidity=validated["soil_humidity"],
                ph_level=validated.get("ph_level"),
            )
            created["soil"] = True
        Device.objects.filter(pk=device.pk).update(
            last_seen=timezone.now(), status="online"
        )
    return created


def ingest_legacy_batch(items: list[dict]) -> dict:
    """Ingiere un lote wide-table. Retorna aceptados + plantas sin binding."""
    accepted = 0
    skipped: list[str] = []
    for item in items:
        try:
            ingest_legacy_reading(item)
        except PlantNotBoundError:
            skipped.append(str(item.get("plant_id")))
        else:
            accepted += 1
    return {"accepted": accepted, "skipped": skipped}
