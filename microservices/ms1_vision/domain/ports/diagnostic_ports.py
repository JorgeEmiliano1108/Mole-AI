from abc import ABC, abstractmethod
from typing import Optional

from ms1_vision.domain.schemas import VisionOutputModel, DiagnosticModel


class VisionClientPort(ABC):
    @abstractmethod
    def analyze(self, image_bytes: bytes) -> VisionOutputModel:
        """Analyze image bytes and return a VisionOutputModel."""


class DiagnosticRepositoryPort(ABC):
    @abstractmethod
    def save_diagnostic(self, diagnostic: DiagnosticModel) -> Optional[int]:
        """Persist diagnostic and return an identifier (or None)."""
