from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..domain.models import ImageAnalysis, VectorDocument

class ImageStoragePort(ABC):
    """Puerto para almacenamiento de imágenes"""
    
    @abstractmethod
    async def save_image(self, image_id: str, image_bytes: bytes, metadata: Dict[str, Any]) -> bool:
        """Guarda imagen en almacenamiento"""
        pass
    
    @abstractmethod
    async def get_image(self, image_id: str) -> bytes:
        """Recupera imagen del almacenamiento"""
        pass

class VisionRepositoryPort(ABC):
    """Puerto para persistencia de resultados de visión"""
    
    @abstractmethod
    async def save_analysis(self, analysis: ImageAnalysis) -> bool:
        """Guarda resultado del análisis"""
        pass
    
    @abstractmethod
    async def get_analysis(self, image_id: str) -> ImageAnalysis:
        """Recupera análisis anterior"""
        pass
    
    @abstractmethod
    async def search_similar_images(self, image_vector: List[float], limit: int = 5) -> List[VectorDocument]:
        """Busca imágenes similares por vector"""
        pass