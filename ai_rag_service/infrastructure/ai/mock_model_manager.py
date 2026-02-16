"""
Infrastructure AI - Mock Model Manager for testing
"""
import time
from typing import Dict, Any

from domain.ports import ModelManagerPort
from domain.models import ModelStatus
from .mock_embeddings import MockEmbeddingAdapter
from .mock_llm import MockLLMAdapter

class MockModelManagerAdapter(ModelManagerPort):
    """Mock implementation of ModelManagerPort for testing"""
    
    def __init__(self):
        self.startup_time = time.time()
        self.embedding_service = MockEmbeddingAdapter()
        self.llm_service = MockLLMAdapter()
    
    async def load_all_models(self) -> Dict[str, bool]:
        """Load all mock AI models"""
        results = {}
        
        try:
            await self.embedding_service.load_model()
            results["embedding"] = True
        except Exception:
            results["embedding"] = False
        
        try:
            await self.llm_service.load_model()
            results["llm"] = True
        except Exception:
            results["llm"] = False
        
        return results
    
    async def unload_all_models(self) -> None:
        """Unload all models"""
        await self.embedding_service.unload_model()
        await self.llm_service.unload_model()
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get mock service health"""
        embedding_status = await self.embedding_service.get_model_status()
        llm_status = await self.llm_service.get_model_status()
        
        uptime_seconds = time.time() - self.startup_time
        is_healthy = embedding_status.is_loaded and llm_status.is_loaded
        
        return {
            "is_healthy": is_healthy,
            "uptime_seconds": round(uptime_seconds, 2),
            "version": "1.0.0-mock",
            "models_status": [
                {
                    "model": embedding_status.model,
                    "is_loaded": embedding_status.is_loaded,
                    "loading_time_ms": embedding_status.loading_time_ms,
                    "memory_usage_mb": embedding_status.memory_usage_mb
                },
                {
                    "model": llm_status.model,
                    "is_loaded": llm_status.is_loaded,
                    "loading_time_ms": llm_status.loading_time_ms,
                    "memory_usage_mb": llm_status.memory_usage_mb
                }
            ]
        }
    
    def get_embedding_service(self):
        """Get embedding service instance"""
        return self.embedding_service
    
    def get_llm_service(self):
        """Get LLM service instance"""
        return self.llm_service