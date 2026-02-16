"""
Application Layer - Use Cases (Orchestration of domain logic)
"""
import logging
import time
from typing import Dict, Any, List

from domain.models import (
    EmbeddingRequest, EmbeddingResponse, 
    ChatRequest, ChatResponse, 
    ModelStatus, ServiceHealth
)
from domain.ports import EmbeddingPort, LLMGenerationPort, ModelManagerPort

logger = logging.getLogger(__name__)


class GenerateEmbeddingUseCase:
    """Use case for generating text embeddings"""
    
    def __init__(self, embedding_service: EmbeddingPort):
        self.embedding_service = embedding_service
    
    async def execute(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Execute embedding generation with timing"""
        start_time = time.time()
        
        try:
            logger.info(f"Generating embedding for text: {request.text[:50]}...")
            response = await self.embedding_service.generate_embedding(request)
            
            processing_time = (time.time() - start_time) * 1000
            response.processing_time_ms = processing_time
            
            logger.info(f"Embedding generated: {response.dimension}D in {processing_time:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Error in GenerateEmbeddingUseCase: {str(e)}")
            raise


class GenerateChatUseCase:
    """Legacy chat use case - DEPRECATED in favor of MoleAIChatUseCase"""
    
    def __init__(self, llm_service: LLMGenerationPort):
        self.llm_service = llm_service
    
    async def execute(self, request: ChatRequest) -> ChatResponse:
        """Execute generic chat generation with timing"""
        start_time = time.time()
        
        try:
            logger.warning(f"Using DEPRECATED GenerateChatUseCase. Consider migrating to MoleAIChatUseCase.")
            response = await self.llm_service.generate_response(request)
            
            processing_time = (time.time() - start_time) * 1000
            response.processing_time_ms = processing_time
            
            logger.info(f"Generic response generated in {processing_time:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Error in GenerateChatUseCase: {str(e)}")
            raise

# NOTE: MoleAIChatUseCase has been moved to application/use_cases/mole_ai_chat_use_case.py
# The duplicate definition was removed to avoid class name collisions.


class GetServiceHealthUseCase:
    """Use case for getting service health status"""
    
    def __init__(self, model_manager: ModelManagerPort):
        self.model_manager = model_manager
    
    async def execute(self) -> ServiceHealth:
        """Execute health check"""
        try:
            health_data = await self.model_manager.get_service_health()
            
            # models_status may contain ModelStatus objects or dicts
            raw_models = health_data.get("models_status", [])
            models_list = []
            for model_data in raw_models:
                if isinstance(model_data, ModelStatus):
                    models_list.append(model_data)
                elif isinstance(model_data, dict):
                    models_list.append(ModelStatus(**model_data))
            
            return ServiceHealth(
                is_healthy=health_data.get("is_healthy", False),
                models_status=models_list,
                uptime_seconds=health_data.get("uptime_seconds", 0.0),
                version=health_data.get("version", "unknown")
            )
            
        except Exception as e:
            logger.error(f"Error in GetServiceHealthUseCase: {str(e)}")
            # Return degraded health status
            return ServiceHealth(
                is_healthy=False,
                models_status=[],
                uptime_seconds=0.0,
                version="error"
            )