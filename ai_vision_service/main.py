"""
Mole AI - Vision Service
Microservicio de análisis visual con Phi-3.5 Vision-Instruct Q4
Arquitectura Hexagonal
"""

import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .infrastructure import settings
from .adapters.outbound import Phi3VisionAdapter
from .adapters.inbound import create_vision_router
from .use_cases import AnalyzePlantVisionUseCase

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# INICIALIZACIÓN GLOBAL
# ============================================================================

phi3_adapter: Phi3VisionAdapter = None
use_case: AnalyzePlantVisionUseCase = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle de aplicación: startup y shutdown"""
    global phi3_adapter, use_case
    
    try:
        logger.info("🚀 Iniciando Vision Service...")
        
        # Inicializar adaptador Phi-3.5
        logger.info("📦 Inicializando Phi-3.5...")
        phi3_adapter = Phi3VisionAdapter(model_name=settings.model_name)
        await phi3_adapter.initialize()
        
        # Crear use case con inyección de dependencias
        use_case = AnalyzePlantVisionUseCase(vision_model=phi3_adapter)
        
        logger.info("✅ Vision Service listo")
        yield
        
    except Exception as e:
        logger.error(f"❌ Error en inicialización: {str(e)}")
        raise
    finally:
        logger.info("🔄 Cerrando Vision Service...")


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """Información del servicio"""
    return {
        "name": "Mole AI - Vision Service",
        "version": "1.0.0",
        "model": "Phi-3.5 Vision-Instruct Q4",
        "description": "Microservicio de análisis visual de plantas (Arquitectura Hexagonal)",
        "endpoints": {
            "analyze": "POST /vision/analyze",
            "health": "GET /vision/health",
            "docs": "GET /docs",
            "redoc": "GET /redoc"
        }
    }


# Registrar router de visión
def init_routes():
    """Inicializa routes con use_case"""
    router = create_vision_router(use_case)
    app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    
    # Inicializar routes después del lifespan
    init_routes()
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )
