"""
ExplainPhUseCase — Hybrid AI Explainability Engine
====================================================
Combines:
  • Black Box  → ph_cnn float from TFLite regression (HSV colorimetry on Edge Node)
  • White Box  → botanical pH tolerance rules + SensorValidator thresholds
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Hardcoded tolerance table (MVP — Capa Blanca simbólica).
# Supabase is always queried first; this is the final safe fallback.
# ──────────────────────────────────────────────────────────────────────────────
PH_TOLERANCE_DB: dict[str, dict] = {
    "Zea mays":               {"min": 5.8, "max": 7.0, "optimal": 6.5},
    "Solanum lycopersicum":   {"min": 5.5, "max": 7.5, "optimal": 6.2},
    "Phaseolus vulgaris":     {"min": 6.0, "max": 7.5, "optimal": 6.8},
    "Capsicum annuum":        {"min": 6.0, "max": 6.8, "optimal": 6.4},
    "Cucurbita pepo":         {"min": 6.0, "max": 7.5, "optimal": 6.8},
    "Solanum tuberosum":      {"min": 4.8, "max": 6.0, "optimal": 5.5},
    "Mangifera indica":       {"min": 5.5, "max": 7.5, "optimal": 6.0},
    "default":                {"min": 5.5, "max": 8.0, "optimal": 6.5},
}


@dataclass
class PhExplanationResult:
    ph_raw: float           # Raw TFLite output
    ph_status: str          # "optimal" | "warning" | "critical"
    deviation: float        # Distance from optimal (+ = alkaline, - = acidic)
    reasoning: str          # Human-readable explanation for the farmer
    recommendations: list[str]
    sensor_context: dict    # ESP32 telemetry + derived alerts
    species_used: str
    confidence: str         # "high" (supabase) | "medium" (external API) | "low" (default)
    data_sources: list[str] = field(default_factory=list)


class ExplainPhUseCase:
    """
    Hybrid Explainability Engine (White Box + Black Box).

    Flow:
      1. Receive ph_cnn (float) + sensors dict + optional species_name
      2. Query Supabase PlantKnowledge for pH tolerance  (Capa Cero)
      3. Cache miss → BotanicalFallbackGateway (Trefle / FarmVillage parallel)
                   → persist result back to Supabase (idempotent)
      4. Classify ph_cnn against tolerance band → status + deviation
      5. Cross-check with SensorValidator alerts (temp, humidity)
      6. Return PhExplanationResult — fully auditable, no opacity
    """

    def __init__(self, knowledge_repo, botanical_gateway, sensor_validator):
        self.knowledge_repo = knowledge_repo       # Port → Supabase PlantKnowledge
        self.botanical_gateway = botanical_gateway # Port → Trefle + FarmVillage
        self.sensor_validator = sensor_validator   # Already exists in project

    async def execute(
        self,
        ph_cnn: float,
        plant_id: str,
        sensors: dict,
        species_name: Optional[str] = None,
    ) -> PhExplanationResult:
        sensors = sensors or {}

        # Step 1 — Resolve tolerance (Capa Cero first)
        tolerance, sources, confidence = await self._get_tolerance(species_name)

        # Step 2 — Compute status
        deviation = round(ph_cnn - tolerance["optimal"], 2)
        ph_status = self._classify_ph(ph_cnn, tolerance)

        # Step 3 — Build human-readable reasoning (White Box)
        reasoning = self._build_reasoning(ph_cnn, tolerance, ph_status, deviation)

        # Step 4 — Cross-check with ESP32 sensor alerts
        sensor_alerts = self._get_sensor_alerts(sensors)
        recommendations = self._build_recommendations(ph_status, deviation, sensor_alerts)

        return PhExplanationResult(
            ph_raw=ph_cnn,
            ph_status=ph_status,
            deviation=deviation,
            reasoning=reasoning,
            recommendations=recommendations,
            sensor_context={**sensors, "alerts": sensor_alerts},
            species_used=species_name or "default",
            confidence=confidence,
            data_sources=sources,
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    async def _get_tolerance(self, species_name: Optional[str]) -> tuple[dict, list[str], str]:
        if species_name:
            # 1. Supabase (Capa Cero)
            try:
                cached = await self.knowledge_repo.get_ph_tolerance(species_name)
                if cached:
                    return cached, ["supabase_cache"], "high"
            except Exception as e:
                logger.warning("Supabase tolerance lookup failed: %s", e)

            # 2. External fallback — persist on cache miss so next call is free
            try:
                external = await self.botanical_gateway.fetch_tolerance(species_name)
                if external:
                    try:
                        await self.knowledge_repo.save_ph_tolerance(species_name, external)
                    except Exception as e:
                        logger.warning("Could not persist tolerance to Supabase: %s", e)
                    return external, ["botanical_gateway", "supabase_saved"], "medium"
            except Exception as e:
                logger.warning("Botanical gateway failed: %s", e)

            # 3a. Named species in hardcoded table
            if species_name in PH_TOLERANCE_DB:
                return PH_TOLERANCE_DB[species_name], ["hardcoded_table"], "low"

        # 3b. Generic safe default (never raises)
        return PH_TOLERANCE_DB["default"], ["hardcoded_default"], "low"

    @staticmethod
    def _classify_ph(ph: float, tol: dict) -> str:
        if tol["min"] <= ph <= tol["max"]:
            return "optimal" if abs(ph - tol["optimal"]) <= 0.5 else "warning"
        return "critical"

    @staticmethod
    def _build_reasoning(ph: float, tol: dict, status: str, dev: float) -> str:
        direction = "alcalino" if dev > 0 else "ácido"
        return (
            f"El modelo de visión (CNN) detectó pH={ph} mediante colorimetría HSV. "
            f"Para esta especie el rango seguro es [{tol['min']}, {tol['max']}] "
            f"con óptimo en {tol['optimal']} pH. "
            f"El suelo está {abs(dev):.2f} unidades hacia el lado {direction}. "
            f"Estado: {status.upper()}."
        )

    def _get_sensor_alerts(self, sensors: dict) -> list[str]:
        """Cross-check sensor readings against physical limits.

        If a SensorValidator is injected, build a SensorData object and run
        validation.  ValidationError messages become alerts.  Otherwise fall
        back to simple threshold rules so the use case never crashes.
        """
        alerts: list[str] = []
        air_temperature = sensors.get("air_temperature", sensors.get("temperature"))
        # Wide table uses soil_humidity; keep humidity as legacy fallback if present.
        humidity = sensors.get("humidity", sensors.get("soil_humidity"))
        if self.sensor_validator is not None:
            try:
                from domain.models import SensorData
                data = SensorData(
                    temperature=air_temperature,
                    air_temperature=air_temperature,
                    humidity=humidity,
                    uv_index=sensors.get("uv_index"),
                    soil_humidity=sensors.get("soil_humidity"),
                    ph_level=sensors.get("ph_level"),
                )
                self.sensor_validator.validate(data)
                # If validate() did not raise, values are within range — no alerts
                return alerts
            except Exception as exc:
                # ValidationError → the message IS the alert
                alerts.append(str(exc))
                return alerts

        # Fallback — basic rules when no validator is available
        if air_temperature is not None and air_temperature > 35:
            alerts.append(f"ESTRÉS TÉRMICO SEVERO — temperatura {air_temperature}°C supera 35°C.")
        if humidity is not None and humidity < 20:
            alerts.append(f"DESHIDRATACIÓN CRÍTICA — humedad {humidity}% por debajo de 20%.")
        return alerts

    @staticmethod
    def _build_recommendations(status: str, deviation: float, alerts: list[str]) -> list[str]:
        recs = []
        if status == "critical":
            if deviation < 0:
                recs.append("Aplicar cal agrícola (CaCO₃) para elevar el pH.")
            else:
                recs.append("Aplicar azufre elemental o vinaza para reducir el pH.")
        elif status == "warning":
            recs.append("Monitorear pH cada 48h y evitar fertilizantes que alteren el suelo.")
        for alert in alerts:
            recs.append(f"⚠️ {alert}")
        return recs
