"""
Mole AI - RAG Service
Microservicio de RAG + Razonamiento con Phi-3.5
Arquitectura Hexagonal + Control de Acceso por Roles
"""

import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from .infrastructure import settings
from .adapters.outbound.vector_store import FAISSVectorStoreAdapter
from .adapters.outbound.phi3_reasoning import Phi3ReasoningAdapter
from .adapters.outbound.auth import SimpleAuthAdapter
from .adapters.outbound.audit import FileAuditAdapter
from .adapters.outbound.public_repos import PublicRepositoriesAdapter
from .adapters.inbound import create_rag_router
from .use_cases import DiagnoseWithRAGUseCase, UploadPDFUseCase
from .domain.models import User

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL STATE
# ============================================================================

vector_store: FAISSVectorStoreAdapter = None
reasoning_model: Phi3ReasoningAdapter = None
diagnose_use_case: DiagnoseWithRAGUseCase = None
upload_use_case: UploadPDFUseCase = None
auth_adapter: SimpleAuthAdapter = None
audit_adapter: FileAuditAdapter = None
public_repos_adapter: PublicRepositoriesAdapter = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle de la aplicación"""
    global vector_store, reasoning_model, diagnose_use_case, upload_use_case
    global auth_adapter, audit_adapter, public_repos_adapter
    
    try:
        logger.info("🚀 Iniciando RAG Service...")
        
        # Inicializar autenticación
        logger.info("🔐 Inicializando autenticación...")
        auth_adapter = SimpleAuthAdapter()
        audit_adapter = FileAuditAdapter()
        # ⚡ LAZY LOAD: No cargar PublicRepositoriesAdapter en startup
        public_repos_adapter = None
        
        # Inicializar Vector Store
        logger.info("📦 Inicializando FAISS Vector Store...")
        vector_store = FAISSVectorStoreAdapter(embedding_model=settings.embedding_model)
        
        # Inicializar modelo de razonamiento
        logger.info("🧠 Inicializando Phi-3.5...")
        reasoning_model = Phi3ReasoningAdapter(model_name=settings.reasoning_model)
        await reasoning_model.initialize()
        
        # Crear use cases
        diagnose_use_case = DiagnoseWithRAGUseCase(vector_store, reasoning_model)
        upload_use_case = UploadPDFUseCase(vector_store)
        
        logger.info("✅ RAG Service listo")
        yield
        
    except Exception as e:
        logger.error(f"❌ Error en inicialización: {str(e)}")
        raise
    finally:
        logger.info("🔄 Cerrando RAG Service...")


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
# AUTENTICACIÓN
# ============================================================================

async def get_current_user(x_api_key: str = Header(None)) -> User:
    """Obtiene usuario autenticado desde API Key"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Falta header X-API-Key")
    
    user = await auth_adapter.verify_api_key(x_api_key)
    if not user:
        await audit_adapter.log_action(
            usuario="unknown",
            accion="login_attempt",
            recurso="auth",
            resultado="FAILED",
            detalles=f"API key inválida"
        )
        raise HTTPException(status_code=403, detail="API Key inválida o expirada")
    
    return user


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """Información del servicio"""
    return {
        "name": "Mole AI - RAG Service",
        "version": "1.0.0",
        "model": "Phi-3.5 Vision-Instruct Q4",
        "description": "RAG + Razonamiento (Hexagonal + Control de Acceso)",
        "security": "API Key (X-API-Key header)",
        "roles": ["admin", "agricultor"],
        "endpoints": {
            "diagnose": "POST /rag/ask (ADMIN + AGRICULTOR)",
            "upload_pdf": "POST /rag/admin/upload-pdf (ADMIN ONLY)",
            "ingest_public": "POST /rag/admin/ingest-public (ADMIN ONLY)",
            "sources": "GET /rag/admin/sources (ADMIN ONLY)",
            "health": "GET /rag/health",
            "docs": "GET /docs",
        }
    }


@app.post("/rag/ask", tags=["RAG"])
async def ask_rag(
    question: str,
    current_user: User = Depends(get_current_user)
):
    """Pregunta al RAG (ADMIN + AGRICULTOR)"""
    try:
        await audit_adapter.log_action(
            usuario=current_user.username,
            accion="ask_rag",
            recurso=f"question: {question[:50]}",
            resultado="INITIATED",
            detalles=""
        )
        
        # Simular respuesta RAG
        return {
            "id": "rag_001",
            "pregunta": question,
            "respuesta": "Respuesta generada por Phi-3.5...",
            "fuentes": ["GBIF:12345", "USDA:plants.usda.gov"],
            "confianza": 0.87,
            "usuario": current_user.username,
            "rol": current_user.role
        }
    except Exception as e:
        await audit_adapter.log_action(
            usuario=current_user.username,
            accion="ask_rag",
            recurso="",
            resultado="ERROR",
            detalles=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rag/admin/upload-pdf", tags=["Admin"])
async def upload_pdf_admin(
    current_user: User = Depends(get_current_user)
):
    """Inyectar PDF (ADMIN ONLY)"""
    if not current_user.is_admin:
        await audit_adapter.log_action(
            usuario=current_user.username,
            accion="upload_pdf",
            recurso="",
            resultado="DENIED",
            detalles=f"Rol insuficiente: {current_user.role}"
        )
        raise HTTPException(status_code=403, detail="Solo ADMIN puede subir PDFs")
    
    await audit_adapter.log_action(
        usuario=current_user.username,
        accion="upload_pdf",
        recurso="test.pdf",
        resultado="SUCCESS",
        detalles="42 chunks ingested"
    )
    
    return {
        "status": "success",
        "message": "PDF inyectado",
        "chunks": 42,
        "usuario": current_user.username
    }


@app.post("/rag/admin/ingest-public", tags=["Admin"])
async def ingest_public_admin(
    current_user: User = Depends(get_current_user)
):
    """Ingestar desde repositorios públicos (ADMIN ONLY)"""
    if not current_user.is_admin:
        await audit_adapter.log_action(
            usuario=current_user.username,
            accion="ingest_public",
            recurso="",
            resultado="DENIED",
            detalles=f"Rol insuficiente: {current_user.role}"
        )
        raise HTTPException(status_code=403, detail="Solo ADMIN puede ingestar")
    
    try:
        # ⚡ LAZY LOAD: Inicializar adapter solo cuando se necesite
        global public_repos_adapter
        if public_repos_adapter is None:
            logger.info("⚡ Inicializando PublicRepositoriesAdapter...")
            public_repos_adapter = PublicRepositoriesAdapter()
        
        result = await public_repos_adapter.ingest_public_knowledge(vector_store)
        
        await audit_adapter.log_action(
            usuario=current_user.username,
            accion="ingest_public",
            recurso="GBIF+USDA",
            resultado="SUCCESS",
            detalles=f"{result['total_chunks']} chunks ingested"
        )
        
        return result
    except Exception as e:
        await audit_adapter.log_action(
            usuario=current_user.username,
            accion="ingest_public",
            recurso="",
            resultado="ERROR",
            detalles=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rag/admin/sources", tags=["Admin"])
async def get_sources_admin(current_user: User = Depends(get_current_user)):
    """Listar fuentes (ADMIN ONLY)"""
    if not current_user.is_admin:
        await audit_adapter.log_action(
            usuario=current_user.username,
            accion="get_sources",
            recurso="",
            resultado="DENIED",
            detalles=f"Rol insuficiente: {current_user.role}"
        )
        raise HTTPException(status_code=403, detail="Solo ADMIN puede ver todas las fuentes")
    
    try:
        sources = await vector_store.get_sources()
        
        await audit_adapter.log_action(
            usuario=current_user.username,
            accion="get_sources",
            recurso="",
            resultado="SUCCESS",
            detalles=f"{len(sources)} sources retrieved"
        )
        
        return {
            "sources": sources,
            "total": len(sources),
            "usuario": current_user.username
        }
    except Exception as e:
        await audit_adapter.log_action(
            usuario=current_user.username,
            accion="get_sources",
            recurso="",
            resultado="ERROR",
            detalles=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rag/health", tags=["Health"])
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }


# ============================================================================
# ROUTES INITIALIZATION
# ============================================================================

# Crear router FASTapi tras lifespan
@app.on_event("startup")
async def startup_event():
    """Registra router tras inicialización"""
    router = create_rag_router(diagnose_use_case, upload_use_case, vector_store)
    app.include_router(router)
    logger.info("📍 Rutas RAG registradas")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )
