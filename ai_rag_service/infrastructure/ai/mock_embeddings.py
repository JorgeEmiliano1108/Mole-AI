"""
Mock version of embeddings service for testing without dependencies
"""
import asyncio
import time
import random

from domain.models import EmbeddingRequest, EmbeddingResponse, ModelStatus, ModelType
from domain.ports import EmbeddingPort

class MockEmbeddingAdapter(EmbeddingPort):
    """Mock implementation for testing"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or ModelType.SENTENCE_TRANSFORMER
        self.is_loaded = False
        self.loading_time_ms = None
        self.memory_usage_mb = None
        
    async def generate_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate mock 768-dimensional embedding"""
        if not self.is_loaded:
            raise RuntimeError("Embedding model not loaded")
        
        # Generate mock 768-dimensional vector
        vector = [random.uniform(-1, 1) for _ in range(768)]
        
        return EmbeddingResponse(
            vector=vector,
            dimension=768,
            model_used=self.model_name
        )
    
    async def get_model_status(self) -> ModelStatus:
        """Get mock model status"""
        return ModelStatus(
            model=self.model_name,
            is_loaded=self.is_loaded,
            loading_time_ms=self.loading_time_ms,
            memory_usage_mb=100.0  # Mock value
        )
    
    async def load_model(self) -> None:
        """Mock model loading"""
        if self.is_loaded:
            return
        
        start_time = time.time()
        # Simulate loading time
        await asyncio.sleep(0.1)
        
        self.is_loaded = True
        self.loading_time_ms = (time.time() - start_time) * 1000
    
    async def unload_model(self) -> None:
        """Mock model unloading"""
        self.is_loaded = False