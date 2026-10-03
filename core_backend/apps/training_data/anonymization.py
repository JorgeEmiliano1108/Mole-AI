"""Servicio de anonimización de datasets de entrenamiento (Track B).

Convierte registros sensibles (p. ej. AIDiagnostic) en registros de la tabla
espejo `training_dataset_anon`, estrictamente sin PII:
  - Se omite el FK de usuario y `image_path`.
  - Los identificadores se reemplazan por HMAC-SHA256 con clave inyectada por
    variable de entorno (`ANONIMIZACION_KEY`).

La persistencia se delega al Repository Pattern (`repositories.py`).
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from apps.training_data.models import TrainingDatasetAnon
from apps.training_data.repositories import (
    AnonymizationRepository,
    DjangoAnonymizationRepository,
)

logger = logging.getLogger(__name__)


class AnonymizationService:
    """Orquesta la derivación PII → registro anonimizado persistido."""

    def __init__(
        self,
        key: str | None = None,
        repository: AnonymizationRepository | None = None,
    ):
        self._key = key if key is not None else getattr(settings, "ANONIMIZACION_KEY", "")
        if not self._key:
            raise ImproperlyConfigured("ANONIMIZACION_KEY no configurada.")
        self._repo = repository or DjangoAnonymizationRepository()

    def hmac_hex(self, *parts: Any) -> str:
        """HMAC-SHA256 hex del mensaje 'p1|p2|...' con la clave de entorno."""
        message = "|".join(str(p) for p in parts)
        return hmac.new(
            self._key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def anonymize_diagnostic(self, diagnostic: Any) -> TrainingDatasetAnon:
        """Deriva un registro anonimizado desde un AIDiagnostic.

        Campos copiados (solo telemetría clínica, sin PII):
          - diagnosis_label, confidence_score, pvu_reason, metadata, analyzed_at.
        Campos omitidos: user FK, image_path.
        """
        user_id = str(getattr(diagnostic, "user_id", "") or "")
        plant_id = str(getattr(diagnostic, "plant_id", "") or "")
        subject_hash = self.hmac_hex(user_id, plant_id)
        source_fingerprint = self.hmac_hex(str(getattr(diagnostic, "id", "")))

        analyzed_at = getattr(diagnostic, "analyzed_at", None)
        feature_payload: dict[str, Any] = {
            "diagnosis_label": getattr(diagnostic, "diagnosis_label", None),
            "confidence_score": getattr(diagnostic, "confidence_score", None),
            "pvu_reason": getattr(diagnostic, "pvu_reason", None),
            "metadata": getattr(diagnostic, "metadata", None),
            "analyzed_at": analyzed_at.isoformat() if analyzed_at else None,
        }
        record = TrainingDatasetAnon(
            record_type="diagnostic",
            source_fingerprint=source_fingerprint,
            subject_hash=subject_hash,
            feature_payload=feature_payload,
            label=getattr(diagnostic, "diagnosis_label", "") or "",
        )
        saved = self._repo.save(record)
        logger.info("training_dataset_anon_created", extra={"record_type": "diagnostic"})
        return saved
