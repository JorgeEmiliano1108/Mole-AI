"""
Supabase Diagnostic Repository — persists AIDiagnostic & CNNInference
rows via the Supabase PostgREST API.

Tables: ai_diagnostics, cnn_inferences  (managed = False in Django ORM)
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

from domain.ports.diagnostic_ports import DiagnosticRepositoryPort

logger = logging.getLogger(__name__)


class SupabaseDiagnosticRepo(DiagnosticRepositoryPort):
    """Concrete adapter — writes diagnostic/inference rows to Supabase."""

    def __init__(self, supabase_url: str, supabase_key: str, http_client: httpx.AsyncClient):
        self._base = supabase_url.rstrip("/")
        self._headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        self._http = http_client

    # ── Port: save_diagnostic ──────────────────────────────────────────

    async def save_diagnostic(
        self,
        plant_id: str,
        diagnostic_type: str,
        condition_name: str,
        condition_description: str,
        severity: str,
        ai_model_used: str,
        confidence_score: float,
        processing_time_ms: int,
        image_url: str,
        recommendations: list,
        predictions: list,
        confidence_scores: list,
    ) -> int:
        url = f"{self._base}/rest/v1/ai_diagnostics"
        payload = {
            "plant_id": plant_id,
            "diagnostic_type": diagnostic_type,
            "condition_name": condition_name,
            "condition_description": condition_description,
            "severity": severity,
            "ai_model_used": ai_model_used,
            "confidence_score": confidence_score,
            "processing_time_ms": processing_time_ms,
            "image_url": image_url,
            "recommendations": json.dumps(recommendations),
            "predictions": json.dumps(predictions),
            "confidence_scores": json.dumps(confidence_scores),
        }
        try:
            resp = await self._http.post(url, headers=self._headers, json=payload, timeout=10.0)
            resp.raise_for_status()
            rows = resp.json()
            if not rows:
                raise RuntimeError("save_diagnostic: PostgREST returned empty response")
            return rows[0]["id"]
        except httpx.HTTPStatusError as exc:
            logger.error("save_diagnostic HTTP error: %s", exc)
            raise RuntimeError(f"DiagnosticPersistenceError: HTTP {exc.response.status_code}") from exc
        except RuntimeError:
            raise
        except Exception as exc:
            logger.error("save_diagnostic failed: %s", exc)
            raise RuntimeError(f"DiagnosticPersistenceError: {exc}") from exc

    # ── Port: save_cnn_inference ───────────────────────────────────────

    async def save_cnn_inference(
        self,
        diagnostic_id: int,
        image_url: str,
        model_type: str,
        model_name: str,
        predictions: list,
        confidence_scores: list,
        top_prediction: dict,
        inference_time_ms: int,
    ) -> int:
        url = f"{self._base}/rest/v1/cnn_inferences"
        payload = {
            "diagnostic_id": diagnostic_id,
            "image_url": image_url,
            "model_type": model_type,
            "model_name": model_name,
            "predictions": json.dumps(predictions),
            "confidence_scores": json.dumps(confidence_scores),
            "top_prediction": json.dumps(top_prediction),
            "inference_time_ms": inference_time_ms,
        }
        try:
            resp = await self._http.post(url, headers=self._headers, json=payload, timeout=10.0)
            resp.raise_for_status()
            rows = resp.json()
            return rows[0]["id"] if rows else 0
        except Exception as exc:
            logger.error("save_cnn_inference failed: %s", exc)
            return 0
