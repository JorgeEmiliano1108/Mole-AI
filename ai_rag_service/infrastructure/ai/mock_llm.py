"""
Mock version of LLM service for testing without dependencies
"""
import asyncio
import time

from domain.models import ChatRequest, ChatResponse, ModelStatus, ModelType
from domain.ports import LLMGenerationPort

class MockLLMAdapter(LLMGenerationPort):
    """Mock implementation for testing"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or ModelType.PHI35_VISION
        self.is_loaded = False
        self.loading_time_ms = None
        self.memory_usage_mb = None
        
    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        """Generate mock response"""
        if not self.is_loaded:
            raise RuntimeError("LLM model not loaded")
        
        # Generate mock response based on query and context
        context_text = " ".join(request.context) if request.context else ""
        response_text = f"Respuesta generada para: '{request.query}'. "
        if context_text:
            response_text += f"Basado en el contexto: {context_text[:100]}..."
        else:
            response_text += "Sin contexto adicional proporcionado."
        
        return ChatResponse(
            answer=response_text,
            model_used=self.model_name,
            tokens_generated=len(response_text.split())
        )
    
    async def get_model_status(self) -> ModelStatus:
        """Get mock model status"""
        return ModelStatus(
            model=self.model_name,
            is_loaded=self.is_loaded,
            loading_time_ms=self.loading_time_ms,
            memory_usage_mb=200.0  # Mock value
        )
    
    async def load_model(self) -> None:
        """Mock model loading"""
        if self.is_loaded:
            return
        
        start_time = time.time()
        # Simulate loading time
        await asyncio.sleep(0.2)
        
        self.is_loaded = True
        self.loading_time_ms = (time.time() - start_time) * 1000
    
    async def unload_model(self) -> None:
        """Mock model unloading"""
        self.is_loaded = False