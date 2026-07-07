"""
Infrastructure Layer - Adapter: NVIDIA Vision (Llama 3.2 Vision Instruct)
Implementa VisionClientPort. Motor de visión exclusivo.
"""
import base64
import json
import logging
import re
from typing import Optional

import structlog

from app.application.ports import VisionClientPort
from app.domain.entities import (
    PlantDiagnosis, SeverityLevel, AfflictionType,
    GrowthStage, ProgressionStage,
)
from app.infrastructure.adapters.nvidia_client import NvidiaBaseClient
from app.core.config import settings

logger = structlog.get_logger()

_VISION_SYSTEM_PROMPT = """\
You are an expert plant pathologist and agronomist AI. Analyze the provided plant image and respond ONLY with a valid JSON object—no markdown, no explanation—using this exact schema:

{
  "species_common": "<common name in Spanish, e.g. 'Tomate'>",
  "species_scientific": "<scientific name, e.g. 'Solanum lycopersicum', or 'No identificada'>",

  "growth_stage": "<one of: PLANTULA, VEGETATIVA, FLORACION, FRUCTIFICACION, SENESCENCIA, UNKNOWN>",

  "affliction_name": "<specific pest/disease name in Spanish, e.g. 'Tizón tardío', 'Mosca blanca', 'Cenicilla polvorienta'>",
  "affliction_type": "<one of: PEST, FUNGAL, BACTERIAL, VIRAL, NUTRIENT, PHYSIOLOGICAL, UNKNOWN>",
  "causal_agent": "<scientific name of causal agent if known, e.g. 'Phytophthora infestans', or 'Desconocido'>",

  "severity": "<one of: LOW, MEDIUM, HIGH, CRITICAL>",
  "progression": "<one of: INITIAL (<25% affected), ADVANCED (25-70% affected), TERMINAL (>70% affected)>",
  "confidence": <float 0.0-1.0>,

  "immediate_actions": ["<action 1>", "<action 2>"],
  "preventive_measures": ["<action 1>", "<action 2>"],
  "mitigation_steps": ["<step 1>", "<step 2>"],

  "ph_predicted": <float 4.0-8.5 or null>
}

Rules:
1. Detect pests/diseases on ANY plant species and ANY growth stage.
2. For healthy plants: affliction_name="Ninguna", affliction_type="PHYSIOLOGICAL", progression="INITIAL", immediate_actions=[], preventive_measures=["Mantener monitoreo rutinario"], mitigation_steps=[].
3. Be specific about pest/disease names — not generic like "plaga" but "Mosca blanca (Trialeurodes vaporariorum)".
4. Progression must match visible symptom coverage.
5. Recommendations must be actionable, specific, and in Spanish.
6. ph_predicted: analyze leaf colorimetry + visible soil. null if undetectable.
7. NOM-059-SEMARNAT COMPLIANCE: If the identified species is a protected/cactaceae/endangered species under NOM-059, set affliction_name="ESPECIE_PROTEGIDA", affliction_type="UNKNOWN", and include in immediate_actions: ["Consulta la lista oficial SEMARNAT. Esta especie está protegida por la NOM-059."]
Respond with JSON only. No other text."""

_SEVERITY_MAP = {
    "LOW": SeverityLevel.LOW,
    "MEDIUM": SeverityLevel.MEDIUM,
    "HIGH": SeverityLevel.HIGH,
    "CRITICAL": SeverityLevel.CRITICAL,
}

_AFFLICTION_TYPE_MAP = {
    "PEST": AfflictionType.PEST,
    "FUNGAL": AfflictionType.FUNGAL,
    "BACTERIAL": AfflictionType.BACTERIAL,
    "VIRAL": AfflictionType.VIRAL,
    "NUTRIENT": AfflictionType.NUTRIENT,
    "PHYSIOLOGICAL": AfflictionType.PHYSIOLOGICAL,
    "UNKNOWN": AfflictionType.UNKNOWN,
}

_GROWTH_STAGE_MAP = {
    "PLANTULA": GrowthStage.PLANTULA,
    "VEGETATIVA": GrowthStage.VEGETATIVA,
    "FLORACION": GrowthStage.FLORACION,
    "FRUCTIFICACION": GrowthStage.FRUCTIFICACION,
    "SENESCENCIA": GrowthStage.SENESCENCIA,
    "UNKNOWN": GrowthStage.UNKNOWN,
}

_PROGRESSION_MAP = {
    "INITIAL": ProgressionStage.INITIAL,
    "ADVANCED": ProgressionStage.ADVANCED,
    "TERMINAL": ProgressionStage.TERMINAL,
}


class NvidiaVisionAdapter(VisionClientPort):
    """
    Adaptador para inferencia de visión con NVIDIA NIM (meta/llama-3.2-11b-vision-instruct).
    Implementa VisionClientPort de forma asíncrona.
    """

    def __init__(self):
        model = settings.NVIDIA_VISION_MODEL
        self.nim = NvidiaBaseClient(model_name=model)
        logger.info("nvidia_vision_adapter_init", model=model)

    def is_ready(self) -> bool:
        return self.nim.api_key is not None

    async def analyze(self, image_bytes: bytes) -> PlantDiagnosis:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        raw = await self.nim.generate_vision(
            prompt=_VISION_SYSTEM_PROMPT,
            image_b64=image_b64,
            max_tokens=1024,
        )

        return self._parse_response(raw)

    def _parse_response(self, raw: str) -> PlantDiagnosis:
        """
        Parsea la respuesta JSON del VLM al dominio PlantDiagnosis.
        Blindado contra respuestas con markdown o texto extra.
        """
        try:
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in response")

            data = json.loads(json_match.group())

            species_common = str(data.get("species_common", "Desconocida"))
            species_scientific = str(data.get("species_scientific", "No identificada"))

            raw_growth = str(data.get("growth_stage", "UNKNOWN")).upper()
            growth_stage = _GROWTH_STAGE_MAP.get(raw_growth, GrowthStage.UNKNOWN)

            affliction_name = str(data.get("affliction_name", "Ninguna"))

            raw_affliction = str(data.get("affliction_type", "UNKNOWN")).upper()
            affliction_type = _AFFLICTION_TYPE_MAP.get(raw_affliction, AfflictionType.UNKNOWN)

            causal_agent = str(data.get("causal_agent", "Desconocido"))

            raw_severity = str(data.get("severity", "MEDIUM")).upper()
            try:
                severity = SeverityLevel[raw_severity]
            except KeyError:
                severity = SeverityLevel.MEDIUM

            raw_progression = str(data.get("progression", "INITIAL")).upper()
            progression = _PROGRESSION_MAP.get(raw_progression, ProgressionStage.INITIAL)

            confidence = float(data.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))

            immediate = data.get("immediate_actions", [])
            preventive = data.get("preventive_measures", [])
            mitigation = data.get("mitigation_steps", [])
            if not isinstance(immediate, list):
                immediate = []
            if not isinstance(preventive, list):
                preventive = []
            if not isinstance(mitigation, list):
                mitigation = []

            ph_raw = data.get("ph_predicted")
            ph_predicted: Optional[float] = None
            if ph_raw is not None:
                try:
                    ph_predicted = float(ph_raw)
                    ph_predicted = max(0.0, min(14.0, ph_predicted))
                except (ValueError, TypeError):
                    ph_predicted = None

        except Exception as e:
            logger.warning("nvidia_vision_parse_failed", error=str(e), raw_response=raw[:200])
            return PlantDiagnosis(
                plant_id="",
                species_common="Desconocida",
                species_scientific="No identificada",
                growth_stage=GrowthStage.UNKNOWN,
                affliction_name="Error al procesar la respuesta",
                affliction_type=AfflictionType.UNKNOWN,
                causal_agent="Desconocido",
                severity=SeverityLevel.MEDIUM,
                progression=ProgressionStage.INITIAL,
                confidence=0.0,
                immediate_actions=(),
                preventive_measures=(),
                mitigation_steps=(),
                ph_predicted=None,
            )

        return PlantDiagnosis(
            plant_id="",
            species_common=species_common,
            species_scientific=species_scientific,
            growth_stage=growth_stage,
            affliction_name=affliction_name,
            affliction_type=affliction_type,
            causal_agent=causal_agent,
            severity=severity,
            progression=progression,
            confidence=confidence,
            immediate_actions=tuple(immediate),
            preventive_measures=tuple(preventive),
            mitigation_steps=tuple(mitigation),
            ph_predicted=ph_predicted,
        )
