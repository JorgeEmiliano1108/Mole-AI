"""
Ports for the diagnostic pipeline (Sprint 2).
"""
from abc import ABC, abstractmethod
from typing import Optional


class DiagnosticRepositoryPort(ABC):
    """Persists AIDiagnostic and CNNInference records."""

    @abstractmethod
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
        """Persist an AIDiagnostic row and return its ID."""

    @abstractmethod
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
        """Persist a CNNInference row and return its ID."""


class VisionClientPort(ABC):
    """Executes the CNN model (local or remote)."""

    @abstractmethod
    async def analyze(self, image_url: str) -> dict:
        """Return a dict with keys: species, ph, condition, description,
        severity, confidence, predictions, confidence_scores, model_used."""
