"""
Domain Ports - Public exports

"""

# Try to import from interfaces.py, fallback to empty exports
try:
    from ..interfaces import (
        EmbeddingPort,
        LLMGenerationPort, 
        ModelManagerPort,
        AuthenticationPort,
        VectorStorePort,
        KnowledgeIngestionPort,
        PublicRepoPort
    )
    from .knowledge_repository_port import KnowledgeRepositoryPort
    # Alias para compatibilidad
    LLMPort = LLMGenerationPort

    __all__ = [
        'EmbeddingPort',
        'LLMGenerationPort',
        'LLMPort',
        'ModelManagerPort',
        'AuthenticationPort',
        'VectorStorePort',
        'KnowledgeIngestionPort',
        'PublicRepoPort',
        'ReasoningModelPort',
        'KnowledgeRepositoryPort',
    ]
except ImportError as e:
    print(f"⚠️ Error importing ports from interfaces: {e}")
    # Create placeholder classes if import fails to avoid instant crash
    from abc import ABC, abstractmethod
    from typing import Dict, Any, List
    
    class AuthenticationPort(ABC):
        @abstractmethod
        async def get_current_user(self, token: str):
            pass

    class EmbeddingPort(ABC):
        @abstractmethod
        async def generate_embedding(self, request):
            pass
        @abstractmethod
        async def get_model_status(self):
            pass
    
    class LLMGenerationPort(ABC):
        @abstractmethod
        async def generate_response(self, request):
            pass
        @abstractmethod
        async def get_model_status(self):
            pass
            
    LLMPort = LLMGenerationPort
    
    class ModelManagerPort(ABC):
        @abstractmethod
        async def load_all_models(self) -> Dict[str, bool]:
            pass
        @abstractmethod
        async def unload_all_models(self) -> None:
            pass
        @abstractmethod
        async def get_service_health(self) -> Dict[str, Any]:
            pass
    
    class VectorStorePort(ABC):
        @abstractmethod
        async def add_documents(self, documents: List[str], metadata: List[dict]) -> int:
            pass
        @abstractmethod
        async def retrieve(self, query: str, top_k: int = 3):
            pass
        @abstractmethod
        async def get_sources(self) -> List[dict]:
            pass

    class KnowledgeIngestionPort(ABC):
        @abstractmethod
        async def parse_file(self, file_content: bytes, filename: str):
            pass

    class PublicRepoPort(ABC):
        @abstractmethod
        async def fetch_repo_content(self, repo_url: str):
            pass

    __all__ = [
        'EmbeddingPort',
        'LLMGenerationPort', 
        'LLMPort',
        'ModelManagerPort',
        'AuthenticationPort',
        'VectorStorePort',
        'KnowledgeIngestionPort',
        'PublicRepoPort'
    ]