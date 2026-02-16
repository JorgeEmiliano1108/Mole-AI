"""
Domain Ports - Abstract interfaces for infrastructure implementations
(CORREGIDO: Con AuthenticationPort y User)
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .models import (
    EmbeddingRequest, 
    EmbeddingResponse, 
    ChatRequest, 
    ChatResponse, 
    ModelStatus,
    User,
    RAGChunk,
    DiagnoseRequest,
    FinalDiagnosis
)
from typing import Tuple


class AuthenticationPort(ABC):
    """Port for User Authentication"""
    
    @abstractmethod
    async def verify_api_key(self, api_key: str) -> Optional[User]:
        """Verify API key and return user or None"""
        pass

class EmbeddingPort(ABC):
    """Port for text embedding generation"""
    
    @abstractmethod
    async def generate_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embedding vector from text"""
        pass
    
    @abstractmethod
    async def get_model_status(self) -> ModelStatus:
        """Get embedding model status"""
        pass

class LLMGenerationPort(ABC):
    """Port for Large Language Model generation"""
    
    @abstractmethod
    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        """Generate text response using LLM with context"""
        pass
    
    @abstractmethod
    async def get_model_status(self) -> ModelStatus:
        """Get LLM model status"""
        pass

# Alias para compatibilidad con código que busque 'LLMPort'
LLMPort = LLMGenerationPort

class ModelManagerPort(ABC):
    """Port for managing AI model lifecycle"""
    
    @abstractmethod
    async def load_all_models(self) -> Dict[str, bool]:
        """Load all AI models once at startup"""
        pass
    
    @abstractmethod
    async def unload_all_models(self) -> None:
        """Unload all models safely"""
        pass
    
    @abstractmethod
    async def get_service_health(self) -> Dict[str, Any]:
        """Get overall service health"""
        pass

class VectorStorePort(ABC):
    """Port for Vector Store operations (RAG)"""
    
    @abstractmethod
    async def add_documents(self, documents: List[str], metadata: List[dict]) -> int:
        """Add documents to vector store"""
        pass
    
    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 3) -> List['RAGChunk']:
        """Retrieve similar chunks"""
        pass
    
    @abstractmethod
    async def get_sources(self) -> List[dict]:
        """Get list of loaded sources"""
        pass

class KnowledgeIngestionPort(ABC):
    """Port for ingesting knowledge from files (PDF, Text)"""
    
    @abstractmethod
    async def parse_file(self, file_content: bytes, filename: str) -> Tuple[List[str], List[dict]]:
        """Parse file content into chunks and metadata"""
        pass

class PublicRepoPort(ABC):
    """Port for interacting with Public Repositories (Github/HuggingFace)"""
    
    @abstractmethod
    async def fetch_repo_content(self, repo_url: str) -> List[Dict[str, Any]]:
        """Fetch content from public repository"""
        pass

class ReasoningModelPort(ABC):
    """Port for AI reasoning/diagnosis models"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Load and initialize the reasoning model"""
        pass
    
    @abstractmethod
    async def is_ready(self) -> bool:
        """Check if model is ready for inference"""
        pass
    
    @abstractmethod
    async def diagnose(self, request: 'DiagnoseRequest', context: str) -> 'FinalDiagnosis':
        """Generate diagnosis from request and RAG context"""
        pass