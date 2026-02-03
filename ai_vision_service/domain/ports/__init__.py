"""Puertos (interfaces) del dominio"""

from abc import ABC, abstractmethod
from ..models import VisionAnalysisRequest, VisionAnalysisResult


class VisionModelPort(ABC):
    """Puerto para modelo de visión (Phi-3.5)"""
    
    @abstractmethod
    async def analyze_image(self, request: VisionAnalysisRequest) -> VisionAnalysisResult:
        """Analiza imagen y retorna resultado estructurado"""
        pass
    
    @abstractmethod
    async def is_ready(self) -> bool:
        """Verifica si el modelo está listo"""
        pass
