"""
Infrastructure AI - Model Manager
(CORREGIDO: Agregado método initialize para compatibilidad con main.py)
"""
import logging
import time
import asyncio
from typing import Dict, Any, List

# Usamos interfaces en lugar de ports
from domain.interfaces import ModelManagerPort
from domain.models import ModelStatus

# Mantenemos tus importaciones originales de adaptadores
from .embeddings import SentenceTransformerEmbeddingAdapter
from .llm import Phi35LLMAdapter

logger = logging.getLogger(__name__)

class ModelManagerAdapter(ModelManagerPort):
    """Implementation of ModelManagerPort for managing AI model lifecycle"""
    
    def __init__(self):
        self.startup_time = time.time()
        self.embedding_service = None
        self.llm_service = None
        
        # Safe initialization (Degraded mode)
        try:
            self.embedding_service = SentenceTransformerEmbeddingAdapter()
        except Exception as e:
            logger.error(f"Failed to initialize Embedding Adapter: {e}. Running in degraded mode.")

        try:
            self.llm_service = Phi35LLMAdapter()
        except Exception as e:
            logger.error(f"Failed to initialize LLM Adapter: {e}. Running in degraded mode.")
        
        logger.info("Model manager initialized")

    async def initialize(self):
        """
        Required by main.py lifespan.
        Alias for load_all_models to fix the AttributeError.
        """
        logger.info("🚀 ModelManager: Starting background model initialization...")
        # Use asyncio.create_task to run loading in background
        # This prevents blocking the startup of the implementation
        asyncio.create_task(self.load_all_models())
        logger.info("⚡ Background task created. API will be responsive immediately (models will load async).")
    
    async def load_all_models(self) -> Dict[str, bool]:
        """Load all AI models once at startup"""
        results = {}
        
        try:
            # Load embedding model
            if self.embedding_service:
                logger.info("Loading embedding model...")
                await self.embedding_service.load_model()
                results["embedding"] = True
            else:
                logger.warning("Embedding service not initialized (degraded mode). Skipping load.")
                results["embedding"] = False
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            results["embedding"] = False
        
        try:
            # Load LLM model
            if self.llm_service:
                logger.info("Loading LLM model...")
                await self.llm_service.load_model()
                results["llm"] = True
            else:
                 logger.warning("LLM service not initialized (degraded mode). Skipping load.")
                 results["llm"] = False
        except Exception as e:
            logger.error(f"Failed to load LLM model: {str(e)}")
            results["llm"] = False
        
        logger.info(f"Model loading completed: {results}")
        return results
    
    async def unload_all_models(self) -> None:
        """Unload all models safely"""
        try:
            if self.embedding_service:
                await self.embedding_service.unload_model()
            if self.llm_service:
                await self.llm_service.unload_model()
            logger.info("All models unloaded successfully")
        except Exception as e:
            logger.error(f"Error unloading models: {str(e)}")
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get overall service health"""
        try:
            # Get individual model statuses
            embedding_status = await self.embedding_service.get_model_status() if self.embedding_service else ModelStatus(model="unknown (failed init)", is_loaded=False)
            llm_status = await self.llm_service.get_model_status() if self.llm_service else ModelStatus(model="unknown (failed init)", is_loaded=False)
            
            # Calculate uptime
            uptime_seconds = time.time() - self.startup_time
            
            # Determine overall health
            # Nota: Usamos getattr por seguridad si el objeto devuelto no tiene el atributo
            emb_loaded = getattr(embedding_status, 'is_loaded', False)
            llm_loaded = getattr(llm_status, 'is_loaded', False)
            is_healthy = emb_loaded and llm_loaded
            
            # Construimos la respuesta compatible con domain.models.HealthStatus
            # pero devolvemos dict porque main.py parece esperar dict para convertirlo después
            return {
                "is_healthy": is_healthy,
                "uptime_seconds": round(uptime_seconds, 2),
                "version": "1.0.0",
                "models_status": [  # Renombrado de 'models' a 'models_status' para coincidir con domain.models
                    embedding_status,
                    llm_status
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting service health: {str(e)}")
            return {
                "is_healthy": False,
                "uptime_seconds": time.time() - self.startup_time,
                "version": "1.0.0",
                "models_status": []
            }
    
    # Getters for use cases
    def get_embedding_service(self):
        """Get embedding service instance"""
        return self.embedding_service
    
    def get_llm_service(self):
        """Get LLM service instance"""
        return self.llm_service