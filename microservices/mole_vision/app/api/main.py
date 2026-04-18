"""
API Layer - Main Entry Point
Skill 01: Arquitectura Hexagonal - FastAPI App
"""
import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings
from app.api.routers import router

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Mole-Vision API",
        description="Vision CNN Service with Zero-Trust Security",
        version="2.0.0",
    )
    
    app.include_router(router)
    
    # CORS from settings
    allow_origins = []
    if settings.ORIGEN_PERMITIDO:
        allow_origins = [o.strip() for o in settings.ORIGEN_PERMITIDO.split(",") if o.strip()]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["accept", "authorization", "content-type", "x-csrftoken", "x-requested-with"],
    )
    
    @app.on_event("startup")
    async def startup_event():
        """Inicializar recursos al startup."""
        logger = structlog.get_logger()
        logger.info("service_starting", service=settings.SERVICE_NAME)
        
        # Pre-cargar el modelo de visión
        try:
            from app.infrastructure.adapters.tflite_adapter import TFLiteVisionAdapter
            adapter = TFLiteVisionAdapter()
            logger.info("vision_model_loaded", ready=adapter.is_ready())
        except Exception as e:
            logger.error("vision_model_load_failed", error=str(e))
    
    @app.get("/config")
    def config() -> dict:
        """Información de configuración del servicio."""
        return {
            "status": "Production" if not settings.DEBUG else "Development",
            "service": settings.SERVICE_NAME,
        }
    
    return app


app = create_app()