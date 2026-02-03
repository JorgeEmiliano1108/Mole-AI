"""Puertos (interfaces) del dominio"""

from abc import ABC, abstractmethod
from typing import List
from ..models import RAGChunk, DiagnoseRequest, FinalDiagnosis


class VectorStorePort(ABC):
    """Puerto para almacén de vectores (FAISS/Chroma)"""
    
    @abstractmethod
    async def add_documents(self, documents: List[str], metadata: List[dict]) -> int:
        """Agrega documentos al vector store"""
        pass
    
    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 3) -> List[RAGChunk]:
        """Recupera chunks similares"""
        pass
    
    @abstractmethod
    async def get_sources(self) -> List[dict]:
        """Retorna lista de fuentes cargadas"""
        pass


class ReasoningModelPort(ABC):
    """Puerto para modelo de razonamiento (Phi-3.5)"""
    
    @abstractmethod
    async def diagnose(self, request: DiagnoseRequest, context: str) -> FinalDiagnosis:
        """Genera diagnóstico final con razonamiento"""
        pass
    
    @abstractmethod
    async def is_ready(self) -> bool:
        """Verifica si el modelo está listo"""
        pass
