from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import base64
from ..domain.models import ImageAnalysis, AnalysisType, PlantType, HealthStatus

class ImageAnalyzerPort(ABC):
    """Puerto de entrada para análisis de imágenes"""
    
    @abstractmethod
    async def analyze_image_base64(self, image_b64: str, analysis_type: AnalysisType) -> ImageAnalysis:
        """Analiza imagen en formato base64"""
        pass
    
    @abstractmethod
    async def detect_plant_type(self, image_b64: str) -> PlantType:
        """Detecta el tipo de planta"""
        pass
    
    @abstractmethod
    async def detect_health_issues(self, image_b64: str, plant_type: str) -> List[Dict[str, Any]]:
        """Detecta problemas de salud en la planta"""
        pass