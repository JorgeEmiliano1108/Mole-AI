"""
CreateDiagnosticUseCase — CNN Diagnostic Pipeline (Sprint 2)
=============================================================
Orchestrates:
  1. Download the image from Supabase Storage URL.
  2. Run the dual-purpose CNN (species detection + pH regression).
  3. If pH detected → delegate to ExplainPhUseCase for explainability.
  4. Persist results in ai_diagnostics + cnn_inferences.
  5. Return a fully auditable DiagnosticResult.

During MVP/dev, the CNN call is simulated; in production it will call
the HuggingFace Inference API or a local TFLite Edge model.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticResult:
    diagnostic_id: int
    plant_id: str
    species_detected: Optional[str]
    ph_predicted: Optional[float]
    condition_name: str
    condition_description: str
    severity: str
    confidence_score: float
    recommendations: list[str] = field(default_factory=list)
    image_url: str = ""
    ph_explanation: Optional[dict] = None


class CreateDiagnosticUseCase:
    """
    Ports required:
      - diagnostic_repo: persists AIDiagnostic + CNNInference records.
      - vision_client:   executes the CNN model (HF API or local).
      - explain_ph_use_case: optional, for pH explainability chain.
    """

    def __init__(self, diagnostic_repo, vision_client, explain_ph_use_case=None):
        self.diagnostic_repo = diagnostic_repo
        self.vision_client = vision_client
        self.explain_ph_use_case = explain_ph_use_case

    async def execute(
        self,
        plant_id: str,
        storage_url: str,
        species_name: Optional[str] = None,
    ) -> DiagnosticResult:

        start = time.perf_counter()

        # ── Step 1: Run CNN inference ──────────────────────────────────
        inference = await self.vision_client.analyze(storage_url)
        # inference expected shape:
        #   { "species": str|None, "ph": float|None,
        #     "condition": str, "description": str,
        #     "severity": str, "confidence": float,
        #     "predictions": list, "confidence_scores": list }

        species = species_name or inference.get("species")
        ph_predicted = inference.get("ph")
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # ── Step 2: pH Explainability (if available) ───────────────────
        ph_explanation = None
        if ph_predicted is not None and self.explain_ph_use_case is not None:
            try:
                explain_result = await self.explain_ph_use_case.execute(
                    ph_cnn=ph_predicted,
                    plant_id=plant_id,
                    sensors={},
                    species_name=species,
                )
                ph_explanation = {
                    "ph_status": explain_result.ph_status,
                    "deviation": explain_result.deviation,
                    "reasoning": explain_result.reasoning,
                    "recommendations": explain_result.recommendations,
                    "confidence": explain_result.confidence,
                    "data_sources": explain_result.data_sources,
                }
            except Exception as exc:
                logger.warning("ExplainPhUseCase failed: %s", exc)

        # ── Step 3: Persist results ────────────────────────────────────
        diagnostic_id = await self.diagnostic_repo.save_diagnostic(
            plant_id=plant_id,
            diagnostic_type="cnn_vision",
            condition_name=inference.get("condition", "Análisis CNN"),
            condition_description=inference.get("description", ""),
            severity=inference.get("severity", "medium"),
            ai_model_used=inference.get("model_used", "dual-cnn-v1"),
            confidence_score=inference.get("confidence", 0.0),
            processing_time_ms=elapsed_ms,
            image_url=storage_url,
            recommendations=ph_explanation.get("recommendations", []) if ph_explanation else [],
            predictions=inference.get("predictions", []),
            confidence_scores=inference.get("confidence_scores", []),
        )

        await self.diagnostic_repo.save_cnn_inference(
            diagnostic_id=diagnostic_id,
            image_url=storage_url,
            model_type="dual_species_ph",
            model_name=inference.get("model_used", "dual-cnn-v1"),
            predictions=inference.get("predictions", []),
            confidence_scores=inference.get("confidence_scores", []),
            top_prediction={"species": species, "ph": ph_predicted},
            inference_time_ms=elapsed_ms,
        )

        return DiagnosticResult(
            diagnostic_id=diagnostic_id,
            plant_id=plant_id,
            species_detected=species,
            ph_predicted=ph_predicted,
            condition_name=inference.get("condition", "Análisis CNN"),
            condition_description=inference.get("description", ""),
            severity=inference.get("severity", "medium"),
            confidence_score=inference.get("confidence", 0.0),
            recommendations=(
                ph_explanation.get("recommendations", []) if ph_explanation else []
            ),
            image_url=storage_url,
            ph_explanation=ph_explanation,
        )
