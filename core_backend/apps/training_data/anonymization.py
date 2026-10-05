"""Servicio de anonimización de datasets de entrenamiento (Track B).

Convierte registros sensibles (AIDiagnostic, TrainingDocument, TrainingImage)
en registros de la tabla espejo `training_dataset_anon`, estrictamente sin PII.

Arquitectura:
  - KeyProvider / EnvKeyProvider: abstrae el origen de la clave HMAC.
  - Anonymizer: opera HMAC-SHA256 con la clave inyectada.
  - AnonymizationService: orquesta la derivación PII → registro anonimizado
    persistido vía Repository Pattern (`repositories.py`).

La clave sigue viniendo de la variable de entorno `ANONIMIZACION_KEY`
(settings.py:313). La rotación es un ADR pendiente (ADR-0012 §1.5).
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from abc import ABC, abstractmethod
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from apps.training_data.models import TrainingDatasetAnon
from apps.training_data.repositories import (
    AnonymizationRepository,
    DjangoAnonymizationRepository,
)

logger = logging.getLogger(__name__)


class KeyProvider(ABC):
    """Contrato para obtener la clave HMAC de anonimización."""

    @abstractmethod
    def get_key(self) -> str:
        """Retorna la clave como string. Debe fallar cerrado si no está configurada."""
        raise NotImplementedError


class EnvKeyProvider(KeyProvider):
    """Lee `ANONIMIZACION_KEY` desde Django settings."""

    def get_key(self) -> str:
        key = getattr(settings, "ANONIMIZACION_KEY", "")
        if not key:
            raise ImproperlyConfigured("ANONIMIZACION_KEY no configurada.")
        return key


class Anonymizer:
    """Pseudonimización determinista vía HMAC-SHA256."""

    def __init__(self, key_provider: KeyProvider | None = None):
        self._key_provider = key_provider or EnvKeyProvider()
        # Fail-fast: la clave debe existir al construir el componente.
        self._key = self._key_provider.get_key()

    @property
    def key(self) -> str:
        return self._key

    def pseudonymize(self, value: str) -> str:
        """Retorna HMAC-SHA256 hex de *value*."""
        return hmac.new(
            self.key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256
        ).hexdigest()


class AnonymizationService:
    """Orquesta la derivación PII → registro anonimizado persistido."""

    def __init__(
        self,
        key_provider: KeyProvider | None = None,
        repository: AnonymizationRepository | None = None,
    ):
        self._anonymizer = Anonymizer(key_provider)
        self._repo = repository or DjangoAnonymizationRepository()

    def hmac_hex(self, *parts: Any) -> str:
        """HMAC-SHA256 hex del mensaje 'p1|p2|...' (compatible con tests existentes)."""
        message = "|".join(str(p) for p in parts)
        return self._anonymizer.pseudonymize(message)

    def _source_fingerprint(self, record_type: str, source_id: Any) -> str:
        return self._anonymizer.pseudonymize(f"{record_type}:{source_id}")

    def _subject_hash(self, *parts: Any) -> str:
        return self._anonymizer.pseudonymize("|".join(str(p) for p in parts))

    def _get_or_create(
        self, record: TrainingDatasetAnon, purged: bool = False
    ) -> TrainingDatasetAnon:
        existing = self._repo.find_by_source_fingerprint(record.source_fingerprint)
        if existing is not None:
            if purged and not existing.purged:
                existing.purged = True
                self._repo.save(existing)
            return existing
        return self._repo.save(record)

    def anonymize_diagnostic(self, diagnostic: Any, purged: bool = False) -> TrainingDatasetAnon:
        """Deriva un registro anonimizado desde un AIDiagnostic."""
        user_id = str(getattr(diagnostic, "user_id", "") or "")
        plant_id = str(getattr(diagnostic, "plant_id", "") or "")
        source_id = str(getattr(diagnostic, "id", "") or "")

        record = TrainingDatasetAnon(
            record_type="diagnostic",
            source_fingerprint=self._source_fingerprint("diagnostic", source_id),
            subject_hash=self._subject_hash(user_id, plant_id),
            feature_payload={
                "diagnosis_label": getattr(diagnostic, "diagnosis_label", None),
                "confidence_score": getattr(diagnostic, "confidence_score", None),
                "pvu_reason": getattr(diagnostic, "pvu_reason", None),
                "metadata": getattr(diagnostic, "metadata", None),
                "analyzed_at": (
                    diagnostic.analyzed_at.isoformat()
                    if getattr(diagnostic, "analyzed_at", None)
                    else None
                ),
            },
            label=getattr(diagnostic, "diagnosis_label", "") or "",
            purged=purged,
        )
        saved = self._get_or_create(record, purged=purged)
        logger.info("training_dataset_anon_ensured", extra={"record_type": "diagnostic"})
        return saved

    def anonymize_document(self, document: Any, purged: bool = False) -> TrainingDatasetAnon:
        """Deriva un registro anonimizado desde un TrainingDocument."""
        user_id = str(getattr(document, "uploaded_by_id", "") or "")
        source_id = str(getattr(document, "id", "") or "")

        record = TrainingDatasetAnon(
            record_type="document",
            source_fingerprint=self._source_fingerprint("document", source_id),
            subject_hash=self._subject_hash(user_id),
            feature_payload={
                "category": getattr(document, "category", None),
                "language": getattr(document, "language", None),
                "content_type": getattr(document, "content_type", None),
                "file_size": getattr(document, "file_size", None),
            },
            label=getattr(document, "category", "") or "",
            purged=purged,
        )
        saved = self._get_or_create(record, purged=purged)
        logger.info("training_dataset_anon_ensured", extra={"record_type": "document"})
        return saved

    def anonymize_image(self, image: Any, purged: bool = False) -> TrainingDatasetAnon:
        """Deriva un registro anonimizado desde un TrainingImage."""
        user_id = str(getattr(image, "uploaded_by_id", "") or "")
        source_id = str(getattr(image, "id", "") or "")

        record = TrainingDatasetAnon(
            record_type="image",
            source_fingerprint=self._source_fingerprint("image", source_id),
            subject_hash=self._subject_hash(user_id),
            feature_payload={
                "disease_label": getattr(image, "disease_label", None),
                "severity": getattr(image, "severity", None),
                "species_id": str(getattr(image, "species_id", "")) or None,
                "content_type": getattr(image, "content_type", None),
                "file_size": getattr(image, "file_size", None),
            },
            label=getattr(image, "disease_label", "") or "",
            purged=purged,
        )
        saved = self._get_or_create(record, purged=purged)
        logger.info("training_dataset_anon_ensured", extra={"record_type": "image"})
        return saved


def export_user_dataset(user: Any, purged: bool = False) -> tuple[int, list[str]]:
    """Exporta todos los assets entrenables de un usuario a la tabla espejo.

    Retorna (cantidad_creados, fingerprints_creadas/actualizadas).
    """
    from apps.core.models import AIDiagnostic
    from apps.training_data.models import TrainingDocument, TrainingImage

    svc = AnonymizationService()
    created = 0
    fingerprints: list[str] = []

    for diagnostic in AIDiagnostic.objects.filter(user=user):
        rec = svc.anonymize_diagnostic(diagnostic, purged=purged)
        fingerprints.append(rec.source_fingerprint)
        created += 1

    for document in TrainingDocument.objects.filter(uploaded_by=user):
        rec = svc.anonymize_document(document, purged=purged)
        fingerprints.append(rec.source_fingerprint)
        created += 1

    for image in TrainingImage.objects.filter(uploaded_by=user):
        rec = svc.anonymize_image(image, purged=purged)
        fingerprints.append(rec.source_fingerprint)
        created += 1

    return created, fingerprints
