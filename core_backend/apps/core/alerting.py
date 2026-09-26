# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# apps/core/alerting.py — Umbrales de telemetría compartidos (issue N-0).
#
# live_alerts_view (admin, global) y my_alerts_view (scoped por usuario) usan
# los mismos umbrales y mensajes; este módulo evita la deriva entre ambos.
# =============================================================================

SOIL_CRIT = 20.0
SOIL_WARN = 35.0
TEMP_WARN = 30.0
UV_CRIT = 8.0


def push_alert(alerts, tipo, msg, source, recorded_at, device_id=None, plant_id=None):
    alerts.append({
        "tipo": tipo,
        "msg": msg,
        "source": source,
        "recorded_at": recorded_at.isoformat() if recorded_at else None,
        "device_id": str(device_id) if device_id else None,
        "plant_id": str(plant_id) if plant_id else None,
    })


def _binding_of(reading):
    return getattr(reading, 'binding', None)


def _plant_id_of(reading, binding):
    if binding is not None:
        return binding.plant_id
    return getattr(reading, 'plant_id', None)


def push_soil_alerts(alerts, soils, source="soil"):
    """Umbrales de humedad de suelo sobre un queryset de SoilReading
    (o SensorLog legacy con source="sensorlog")."""
    for s in soils:
        b = _binding_of(s)
        dev = b.device if b else None
        pid = _plant_id_of(s, b)
        if s.soil_humidity is not None and s.soil_humidity < SOIL_CRIT:
            push_alert(alerts, "error",
                       f"Humedad por debajo del umbral crítico ({s.soil_humidity}%)",
                       source, s.recorded_at, getattr(dev, 'id', None), pid)
        elif s.soil_humidity is not None and s.soil_humidity < SOIL_WARN:
            push_alert(alerts, "warn", f"Humedad baja detectada ({s.soil_humidity}%)",
                       source, s.recorded_at, getattr(dev, 'id', None), pid)


def push_ambient_alerts(alerts, ambients, source="ambient"):
    """Umbrales ambientales sobre un queryset de AmbientReading
    (o SensorLog legacy con source="sensorlog")."""
    for a in ambients:
        dev_id = getattr(a, 'device_id', None)
        if a.air_temperature is not None and a.air_temperature > TEMP_WARN:
            push_alert(alerts, "warn",
                       f"Fluctuación térmica detectada ({a.air_temperature}°C)",
                       source, a.recorded_at, dev_id)
        if a.uv_index is not None and a.uv_index > UV_CRIT:
            push_alert(alerts, "error", f"Índice UV peligroso detectado ({a.uv_index})",
                       source, a.recorded_at, dev_id)


def stable_info():
    return {"msg": "Monitor Vital estable. Biomasa operando dentro de umbrales.",
            "tipo": "info"}
