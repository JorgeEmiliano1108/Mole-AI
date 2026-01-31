from abc import ABC, abstractmethod
from typing import List

# Contrato para la Base de Datos (Tu antiguo db_manager debe cumplir esto)
class VectorRepository(ABC):
    @abstractmethod
    async def save_document(self, content: str, vector: List[float], metadata: dict):
        """Guarda un documento vectorizado."""
        pass

    @abstractmethod
    async def search_similarity(self, vector: List[float], limit: int = 3) -> List[str]:
        """Busca texto similar basado en vectores."""
        pass

# Contrato para la IA (Tu antiguo client.py debe cumplir esto)
class LLMService(ABC):
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Convierte texto a números."""
        pass

    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """Genera texto respuesta."""
        pass

# Contrato para Visión por Computadora (Nueva para Mole.ai)
class VisionService(ABC):
    @abstractmethod
    async def analyze_image(self, image_bytes: bytes) -> str:
        """Analiza una imagen y devuelve descripción."""
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Convierte texto a números para RAG."""
        pass

    @abstractmethod
    async def generate_analysis(self, prompt: str) -> str:
        """Genera análisis basado en imagen y contexto."""
        pass