"""
Infrastructure AI - Embedding Implementation
"""
import logging
import time
import asyncio
import os
from typing import List

import psutil
from sentence_transformers import SentenceTransformer

from domain.models import EmbeddingRequest, EmbeddingResponse, ModelStatus, ModelType
from domain.ports import EmbeddingPort

logger = logging.getLogger(__name__)


# MAPPER EXPLÍCITO (FIX AUDITORÍA)
MODEL_ID_MAP = {
    ModelType.SENTENCE_TRANSFORMER: "sentence-transformers/all-mpnet-base-v2",
    ModelType.PHI35_VISION: "microsoft/Phi-3.5-vision-instruct"
}

class SentenceTransformerEmbeddingAdapter(EmbeddingPort):
    """Implementation of EmbeddingPort using sentence-transformers"""
    
    def __init__(self, model_name: str = None):
        # 1. Determinar tipo de modelo (Enum)
        self.model_type = model_name or ModelType.SENTENCE_TRANSFORMER
        
        # 2. Resolver ID real de HuggingFace (Priority: Env > Map > Enum Value)
        env_override = os.getenv("EMBEDDING_MODEL_ID")
        if env_override:
            self.model_id = env_override
        else:
            # Usar mapa o fallback a value si es enum
            self.model_id = MODEL_ID_MAP.get(self.model_type, self.model_type.value if hasattr(self.model_type, 'value') else str(self.model_type))
            
        # 3. Validación de tipo (FASE BUILDER FIX)
        if not isinstance(self.model_id, str):
            raise TypeError(f"model_id must be string, got {type(self.model_id)}")

        # 4. Validación de seguridad básica
        if "/" not in self.model_id and "\\" not in self.model_id:
             # Si no tiene slash, podría ser un ID inválido de HF, pero permitimos rutas locales si existen
             if not os.path.exists(self.model_id):
                 logger.warning(f"⚠️ Model ID '{self.model_id}' no parece un repo HF válido ni ruta local.")

        self.model = None
        self.is_loaded = False
        self.loading_time_ms = None
        self.memory_usage_mb = None
        
        logger.info(f"Embedding adapter initialized. Type: {self.model_type}, ID: {self.model_id}")
    
    async def generate_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embedding vector from text"""
        if not self.is_loaded:
            raise RuntimeError("Embedding model not loaded. Call load_model() first.")
        
        try:
            # Generate embedding
            embedding_vector = await self._generate_embedding_async(request.text)
            
            return EmbeddingResponse(
                vector=embedding_vector,
                dimension=len(embedding_vector),
                model_used=self.model_id
            )
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    async def get_model_status(self) -> ModelStatus:
        """Get current model status"""
        if self.is_loaded:
            # Calculate memory usage
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.memory_usage_mb = round(memory_mb, 2)
            except Exception:
                self.memory_usage_mb = None
        
        return ModelStatus(
            model=self.model_id,
            is_loaded=self.is_loaded,
            loading_time_ms=self.loading_time_ms,
            memory_usage_mb=self.memory_usage_mb
        )
    
    async def load_model(self) -> None:
        """Load the embedding model (called once at startup)"""
        if self.is_loaded:
            logger.info("Embedding model already loaded")
            return
        
        try:
            start_time = time.time()
            logger.info(f"Loading embedding model: {self.model_id}")
            
            # Load model in thread pool to avoid blocking
            self.model = await asyncio.to_thread(
                SentenceTransformer,
                self.model_id
            )
            
            self.is_loaded = True
            self.loading_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Embedding model loaded in {self.loading_time_ms:.2f}ms")
            
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {str(e)}")
            raise
    
    async def unload_model(self) -> None:
        """Unload the embedding model"""
        if self.model:
            del self.model
            self.model = None
            self.is_loaded = False
            logger.info("Embedding model unloaded")
    
    async def _generate_embedding_async(self, text: str) -> List[float]:
        """Generate embedding in thread pool to avoid blocking"""
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        # Use sentence-transformers to generate 768-dim embedding
        embedding = await asyncio.to_thread(
            self.model.encode,
            text,
            convert_to_numpy=True
        )
        
        return embedding.tolist()