"""
Mole AI - Backend for Backend Service (Merged & Stable)
FastAPI microservice following Hexagonal Architecture
"""
import logging
import sys
import os
from contextlib import asynccontextmanager
from typing import Optional

# Load .env BEFORE any other imports that use os.getenv
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Rate Limiting
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ============================================================================
# 1. SYS.PATH FIX 
# ============================================================================
# Aseguramos que la raíz del proyecto esté en el path antes de importar nada más

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ============================================================================
# IMPORTS
# ============================================================================
# Importamos adaptadores e interfaces reales

try:
    from application.use_cases.mole_ai_chat_use_case import MoleAIChatUseCase
    from application.use_cases import (
        GenerateEmbeddingUseCase, 
        GenerateChatUseCase, 
        GetServiceHealthUseCase
    )
    from application.use_cases.explain_ph_use_case import ExplainPhUseCase
    from infrastructure.ai.model_manager import ModelManagerAdapter
    from infrastructure.ai.vector_store import FAISSVectorStoreAdapter
    from infrastructure.data.pdf_parser import PDFIngestionAdapter
    from infrastructure.external.botanical_gateway import (
        TrefleAdapter, FarmVillageAdapter, BotanicalFallbackGateway
    )
    from infrastructure.database.supabase_knowledge_repo import SupabaseKnowledgeRepo
    from domain.services.validator_service import SensorValidator
    
    from application.use_cases.ingest_knowledge_use_case import IngestKnowledgeUseCase
    from application.use_cases.create_diagnostic_use_case import CreateDiagnosticUseCase
    from infrastructure.api.routes import create_routes
    from infrastructure.api.knowledge_routes import create_knowledge_routes
    from infrastructure.external.supabase_storage import SupabaseStorageAdapter
    from infrastructure.database.supabase_diagnostic_repo import SupabaseDiagnosticRepo
    from infrastructure.external.mock_vision_client import MockVisionClient
    print("Imports cargados.")
except ImportError as e:
    print(f"ERROR: {e}")
    print("ai_rag_service entorno virtual activo.")
    sys.exit(1) 

# ============================================================================
# LOGGING & GLOBAL STATE
# ============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Contenedor de Dependencias
# ============================================================================
# LIFECYCLE (Gestión de Modelos)
# ============================================================================
# Contenedor de Dependencias Globales
model_manager: Optional[ModelManagerAdapter] = None
vector_store_adapter: Optional[FAISSVectorStoreAdapter] = None
pdf_ingestion_adapter: Optional[PDFIngestionAdapter] = None

embedding_use_case: Optional[GenerateEmbeddingUseCase] = None
chat_use_case: Optional[GenerateChatUseCase] = None
mole_ai_chat_use_case: Optional[MoleAIChatUseCase] = None
health_use_case: Optional[GetServiceHealthUseCase] = None
ingest_knowledge_use_case: Optional[IngestKnowledgeUseCase] = None
explain_ph_use_case: Optional[ExplainPhUseCase] = None
storage_adapter: Optional[object] = None
create_diagnostic_use_case: Optional[object] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa los modelos de IA al arrancar y los limpia al cerrar"""
    global model_manager, vector_store_adapter, pdf_ingestion_adapter
    global embedding_use_case, chat_use_case, mole_ai_chat_use_case, health_use_case, ingest_knowledge_use_case
    global explain_ph_use_case, storage_adapter, create_diagnostic_use_case
    _http_client = None
    
    logger.info("Iniciando Mole AI Service...")
    
    try:
        # 1. Inicializar el Gestor de Modelos (Carga pesada)
        model_manager = ModelManagerAdapter()
        await model_manager.initialize() 
        logger.info("Model Manager inicializado")
        
        # 2. Inicializar Adaptadores de Infraestructura
        vector_store_adapter = FAISSVectorStoreAdapter()
        pdf_ingestion_adapter = PDFIngestionAdapter()

        # 3. Inyectar servicios en los Casos de Uso
        embedding_service = model_manager.get_embedding_service()
        llm_service = model_manager.get_llm_service()

        embedding_use_case = GenerateEmbeddingUseCase(embedding_service)
        chat_use_case = GenerateChatUseCase(llm_service)
        
        # INYECCIÓN DEL CASO DE USO ESPECIALIZADO (Mole-AI)
        mole_ai_chat_use_case = MoleAIChatUseCase(
            llm_service=llm_service,
            vector_store=vector_store_adapter
        )
        
        # Caso de uso de Ingesta
        ingest_knowledge_use_case = IngestKnowledgeUseCase(
            vector_store=vector_store_adapter,
            ingestion_service=pdf_ingestion_adapter
        )
        
        health_use_case = GetServiceHealthUseCase(model_manager)
        
        # 5. Inicializar Botanical Gateway + Capa Cero + ExplainPhUseCase
        import httpx as _httpx
        _http_client = _httpx.AsyncClient()  # closed in finally block
        trefle_adapter = TrefleAdapter(
            api_token=os.getenv("TREFLE_API_TOKEN", ""),
            http_client=_http_client,
        )
        farmvillage_adapter = FarmVillageAdapter(
            api_key=os.getenv("FARMVILLAGE_API_KEY", ""),
            http_client=_http_client,
        )
        botanical_gateway = BotanicalFallbackGateway(trefle_adapter, farmvillage_adapter)
        
        # 6. Capa Cero — Supabase Knowledge Repo (cache de tolerancias pH)
        knowledge_repo = SupabaseKnowledgeRepo(
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_key=os.getenv("SUPABASE_KEY", ""),
            http_client=_http_client,
        )
        
        # 7. SensorValidator — reutilizamos el servicio de dominio existente
        sensor_validator = SensorValidator()
        
        explain_ph_use_case = ExplainPhUseCase(
            knowledge_repo=knowledge_repo,
            botanical_gateway=botanical_gateway,
            sensor_validator=sensor_validator,
        )
        
        # 8. Diagnostic Pipeline — Storage + CNN + Repository
        storage_adapter = SupabaseStorageAdapter(http_client=_http_client)
        diagnostic_repo = SupabaseDiagnosticRepo(
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_key=os.getenv("SUPABASE_KEY", ""),
            http_client=_http_client,
        )
        # Feature flag: VISION_BACKEND=mock (default) | real (future HF/TFLite client)
        _vision_backend = os.getenv("VISION_BACKEND", "mock")
        if _vision_backend == "mock":
            vision_client = MockVisionClient()
        else:
            # TODO: Replace with real VisionClient (HuggingFace Inference API / TFLite Edge)
            logger.warning("VISION_BACKEND=%s not implemented yet, falling back to mock", _vision_backend)
            vision_client = MockVisionClient()
        create_diagnostic_use_case = CreateDiagnosticUseCase(
            diagnostic_repo=diagnostic_repo,
            vision_client=vision_client,
            explain_ph_use_case=explain_ph_use_case,
        )
        
        # 4. REGISTRO DE RUTAS (Ahora dentro del lifespan para asegurar inyección)
        if create_routes:
            logger.info("Configurando rutas y endpoints...")
            api_router = create_routes(
                embedding_use_case=embedding_use_case,
                chat_use_case=chat_use_case,
                mole_ai_chat_use_case=mole_ai_chat_use_case,
                health_use_case=health_use_case,
                ingest_knowledge_use_case=ingest_knowledge_use_case,
                explain_ph_use_case=explain_ph_use_case,
                storage_adapter=storage_adapter,
                create_diagnostic_use_case=create_diagnostic_use_case,
            )
            app.include_router(api_router, prefix="/api/v1")
            
            # Knowledge management routes (PDF ingest, sources)
            knowledge_api = create_knowledge_routes(ingest_knowledge_use_case)
            app.include_router(knowledge_api, prefix="/api/v1")
            
            # Log de rutas
            for route in app.routes:
                methods = ", ".join(route.methods) if hasattr(route, "methods") else "ANY"
                logger.info(f" {methods} {route.path}")
        
        logger.info("Casos de uso listos para recibir peticiones")
        yield # El servicio corre aquí
        
    except Exception as e:
        logger.error(f"Error en inicio: {e}")
        raise e
    finally:
        logger.info("Apagando servicios...")
        if _http_client is not None:
            await _http_client.aclose()
        if model_manager:
            await model_manager.unload_all_models()

# ============================================================================
# FASTAPI APP SETUP
# ============================================================================
app = FastAPI(
    title="Mole AI Service",
    version="1.1.0 (Multimodal)",
    lifespan=lifespan
)

# ============================================================================
# RATE LIMITING - SlowAPI Configuration
# ============================================================================
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Límite de solicitudes alcanzado: {exc.detail}",
            "retry_after": getattr(exc, "retry_after", 60)
        }
    )

@app.get("/", tags=["General"])
async def root():
    """Root endpoint to check service status and redirect to docs"""
    return {
        "service": "Mole AI RAG Service",
        "status": "online",
        "version": "1.1.0",
        "docs_url": "/docs",
        "health_check": "/api/v1/health"
    }

# CORS: Allow all origins in dev. In production, set CORS_ALLOWED_ORIGINS env var.
_cors_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()] if _cors_env else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    # Ajustamos sys.path nuevamente para uvicorn subprocess
    sys.path.append(PROJECT_ROOT)
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)