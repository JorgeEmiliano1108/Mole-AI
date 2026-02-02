from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class DiagnosticPort(ABC):
    """Puerto de entrada para diagnóstico de plantas"""
    
    @abstractmethod
    async def diagnose_plant(
        self, 
        sensor_data: Dict[str, Any], 
        vision_results: Optional[Dict[str, Any]] = None,
        plant_context: str = ""
    ) -> Dict[str, Any]:
        """Realiza diagnóstico completo basado en datos y contexto"""
        pass

class KnowledgeBasePort(ABC):
    """Puerto para gestión de base de conocimiento"""
    
    @abstractmethod
    async def ingest_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Ingresa documento a la base de conocimiento"""
        pass
    
    @abstractmethod
    async def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Busca información relevante en la base de conocimiento"""
        pass
    
    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """Elimina documento de la base de conocimiento"""
        pass

class LLMProviderPort(ABC):
    """Puerto para proveedor de LLM"""
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        context: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Genera respuesta del LLM con configuración específica"""
        pass
    
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Genera embedding para texto"""
        pass

class VectorDBPort(ABC):
    """Puerto para base de datos vectorial"""
    
    @abstractmethod
    async def add_document(self, doc_id: str, content: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Agrega documento con su embedding"""
        pass
    
    @abstractmethod
    async def search_similar(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Busca documentos similares por embedding"""
        pass
    
    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """Elimina documento por ID"""
        pass