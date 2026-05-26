"""
Output Ports (Driven Ports)
Contratos que la Lógica de Negocio usa para comunicarse con BDs, LLMs y Cachés.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.domain.schemas import ChatResponse, SourceMetadata

class LLMClientOutputPort(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> ChatResponse:
        pass

class VectorStoreOutputPort(ABC):
    @abstractmethod
    async def asearch(self, query: str) -> str:
        pass

class SensorCacheOutputPort(ABC):
    @abstractmethod
    async def get_context(self, user_id: str) -> Dict[str, Any]:
        pass

class CitationManagerOutputPort(ABC):
    @abstractmethod
    async def extract_sources(self, context: dict) -> List[SourceMetadata]:
        pass