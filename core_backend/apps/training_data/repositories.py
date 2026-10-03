"""Puertos y adaptadores del Repository Pattern para anonimización de datasets.

Track B: la capa de dominio define el contrato; DjangoAnonymizationRepository
es la implementación ORM concreta. Esto permite reemplazar el backend de
persistencia sin tocar la lógica de anonimización.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from apps.training_data.models import TrainingDatasetAnon


class AnonymizationRepository(ABC):
    """Contrato para almacenar y recuperar registros anonimizados."""

    @abstractmethod
    def save(self, record: TrainingDatasetAnon) -> TrainingDatasetAnon:
        """Persiste un registro anonimizado y lo retorna."""
        raise NotImplementedError

    @abstractmethod
    def find_by_subject_hash(self, subject_hash: str) -> Iterable[TrainingDatasetAnon]:
        """Devuelve los registros asociados a un subject_hash."""
        raise NotImplementedError


class DjangoAnonymizationRepository(AnonymizationRepository):
    """Implementación ORM/Django del repositorio de anonimización."""

    def save(self, record: TrainingDatasetAnon) -> TrainingDatasetAnon:
        record.save()
        return record

    def find_by_subject_hash(self, subject_hash: str) -> Iterable[TrainingDatasetAnon]:
        return TrainingDatasetAnon.objects.filter(subject_hash=subject_hash).order_by("-anonymized_at")
