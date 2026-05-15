"""
Infrastructure Layer - Adapter: NVIDIA Vision (Llama 3.2 Vision Instruct)
Implementa VisionClientPort. Reemplaza TFLiteVisionAdapter.
"""
import base64
import json
import logging
import os
import re
from typing import Optional

import structlog

from app.application.ports import VisionClientPort
from app.domain.entities import DiagnosticResult, SeverityLevel, ConditionCategory
from app.infrastructure.adapters.nvidia_client import NvidiaBaseClient

logger = structlog.get_logger()

_VISION_SYSTEM_PROMPT = """\
You are an expert agronomist AI assistant. Analyze the provided plant image and respond ONLY with a valid JSON object—no markdown, no explanation—using this exact schema:

{
  "species": "<plant species name in Spanish>",
  "condition": "<brief diagnosis in Spanish, e.g. 'Manchas de tizón tardío'>",
  "condition_category": "<one of: HEALTHY, DISEASE, PEST, NUTRIENT_DEFICIENCY, ENVIRONMENTAL_STRESS, UNKNOWN>",
  "severity": "<one of: LOW, MEDIUM, HIGH, CRITICAL>",
  "confidence": <float 0.0-1.0>,
  "ph_estimated": <float 4.0-8.5 or null>
}

For ph_estimated: analyze the colorimetry of leaves and visible soil. Yellowing/brown tips → acidic (4.5-6.0). Lush green → neutral (6.0-7.0). Purple tinge → alkaline (7.0-8.5). If undetectable, use null.
Respond with JSON only. No other text."""


_CATEGORY_MAP = {
    "HEALTHY": ConditionCategory.HEALTHY,
    "DISEASE": ConditionCategory.DISEASE,
    "PEST": ConditionCategory.PEST,
    "NUTRIENT_DEFICIENCY": ConditionCategory.NUTRIENT_DEFICIENCY,
    "ENVIRONMENTAL_STRESS": ConditionCategory.ENVIRONMENTAL_STRESS,
    "UNKNOWN": ConditionCategory.UNKNOWN,
}

_SEVERITY_MAP = {
    "LOW": SeverityLevel.LOW,
    "MEDIUM": SeverityLevel.MEDIUM,
    "HIGH": SeverityLevel.HIGH,
    "CRITICAL": SeverityLevel.CRITICAL,
}


class NvidiaVisionAdapter(VisionClientPort):
    """
    Adaptador para inferencia de visión con NVIDIA NIM (meta/llama-3.2-11b-vision-instruct).
    Implementa VisionClientPort de forma asíncrona.
    """

    def __init__(self):
        model = os.getenv("NVIDIA_VISION_MODEL", "meta/llama-3.2-11b-vision-instruct")
        self.nim = NvidiaBaseClient(model_name=model)
        logger.info("nvidia_vision_adapter_init", model=model)

    def is_ready(self) -> bool:
        return self.nim.api_key is not None

    async def analyze(self, image_bytes: bytes) -> DiagnosticResult:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        raw = await self.nim.generate_vision(
            prompt=_VISION_SYSTEM_PROMPT,
            image_b64=image_b64,
            max_tokens=512,
        )

        return self._parse_response(raw)

    def _parse_response(self, raw: str) -> DiagnosticResult:
        """
        Parsea la respuesta JSON del VLM al dominio interno.
        Blindado contra respuestas con markdown (```json ... ```) o texto extra.
        """
        try:
            # Strip markdown fences if present
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in response")

            data = json.loads(json_match.group())

            species = str(data.get("species", "Desconocida"))
            condition = str(data.get("condition", "No identificada"))

            raw_category = str(data.get("condition_category", "UNKNOWN")).upper()
            condition_category = _CATEGORY_MAP.get(raw_category, ConditionCategory.UNKNOWN)

            raw_severity = str(data.get("severity", "MEDIUM")).upper()
            severity = _SEVERITY_MAP.get(raw_severity, SeverityLevel.MEDIUM)

            confidence = float(data.get("confidence", 0.75))
            confidence = max(0.0, min(1.0, confidence))

            ph_raw = data.get("ph_estimated")
            ph_predicted: Optional[float] = None
            if ph_raw is not None:
                try:
                    ph_predicted = float(ph_raw)
                    ph_predicted = max(0.0, min(14.0, ph_predicted))
                except (ValueError, TypeError):
                    ph_predicted = None

        except Exception as e:
            logger.warning("nvidia_vision_parse_failed", error=str(e), raw_response=raw[:200])
            # Safe fallback — maintains contract integrity
            return DiagnosticResult(
                plant_id="",
                species="Desconocida",
                condition="Error al procesar la respuesta del modelo",
                condition_category=ConditionCategory.UNKNOWN,
                severity=SeverityLevel.MEDIUM,
                confidence=0.0,
                ph_predicted=None,
            )

        return DiagnosticResult(
            plant_id="",
            species=species,
            condition=condition,
            condition_category=condition_category,
            severity=severity,
            confidence=confidence,
            ph_predicted=ph_predicted,
        )
