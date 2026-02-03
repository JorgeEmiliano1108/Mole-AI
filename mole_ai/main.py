"""
Mole AI v2.0 - Diagnóstico de Plantas con Phi-3.5 Vision-Instruct Q4
FastAPI + RAG Dinámico + PostgreSQL
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
import json

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Importar integraciones
from .rag_loader import RAGLoader
from .phi3_integration import Phi3VisionModel

load_dotenv()

# Logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class SensorData(BaseModel):
    """Datos de sensores ESP32"""
    ph: float = Field(..., ge=0, le=14)
    humedad: float = Field(..., ge=0, le=100)
    temp: float = Field(..., ge=-50, le=60)
    uv: float = Field(..., ge=0, le=15)


class DiagnosticRequest(BaseModel):
    """Solicitud de diagnóstico"""
    imagen: str = Field(..., description="Imagen en base64")
    sensores: SensorData
    plant_id: Optional[str] = None


class DiagnosticResponse(BaseModel):
    """Respuesta de diagnóstico"""
    id: str
    plant_id: Optional[str]
    estado: str
    confianza: float
    especie: str
    sintomas: List[str]
    diagnostico: str
    recomendaciones: List[str]
    fuentes: List[str]
    requiere_accion_humana: bool
    timestamp: str


class HealthResponse(BaseModel):
    """Estado del sistema"""
    status: str
    model_ready: bool
    rag_ready: bool
    db_connected: bool
    timestamp: str


class UploadResponse(BaseModel):
    """Respuesta de upload"""
    status: str
    filename: str
    chunks: int
    message: Optional[str]


# ============================================================================
# INICIALIZACIÓN
# ============================================================================

rag_loader: Optional[RAGLoader] = None
phi3_model: Optional[Phi3VisionModel] = None


def get_db_connection():
    """Obtiene conexión a PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "mole_ai_db"),
            user=os.getenv("POSTGRES_USER", "mole_user"),
            password=os.getenv("POSTGRES_PASSWORD", "mole_pass_2026"),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.warning(f"Error conectando a PostgreSQL: {str(e)}")
        return None


async def init_db():
    """Inicializa tablas en PostgreSQL"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.warning("PostgreSQL no disponible, continuando sin persistencia")
            return
        
        cursor = conn.cursor()
        
        # Tabla de diagnósticos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnosticos (
                id UUID PRIMARY KEY,
                plant_id UUID,
                imagen_url VARCHAR(500),
                estado VARCHAR(50) NOT NULL,
                confianza FLOAT NOT NULL,
                especie VARCHAR(100),
                sintomas TEXT,
                diagnostico TEXT NOT NULL,
                recomendaciones TEXT,
                fuentes TEXT,
                sensores JSONB,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("✅ Base de datos inicializada")
        
    except Exception as e:
        logger.warning(f"Error inicializando DB: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle de la aplicación"""
    global rag_loader, phi3_model
    
    try:
        logger.info("🚀 Inicializando Mole AI v2.0...")
        
        # RAG Loader
        logger.info("📦 Inicializando RAG Loader...")
        rag_loader = RAGLoader()
        logger.info("✅ RAG Loader listo")
        
        # Phi-3.5 Model
        logger.info("🧠 Inicializando Phi-3.5 Vision-Instruct Q4...")
        phi3_model = Phi3VisionModel()
        await phi3_model.initialize()
        logger.info("✅ Phi-3.5 listo")
        
        # Database
        logger.info("💾 Inicializando base de datos...")
        await init_db()
        
        logger.info("🎉 Mole AI v2.0 ready!")
        yield
        
    except Exception as e:
        logger.error(f"❌ Error en inicialización: {str(e)}")
        raise
    finally:
        logger.info("🔄 Limpieza de recursos...")


# ============================================================================
# APLICACIÓN FASTAPI
# ============================================================================

app = FastAPI(
    title="Mole AI v2.0 - Diagnóstico de Plantas",
    description="Sistema unificado con Phi-3.5 Vision-Instruct Q4",
    version="2.0.0",
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
# ENDPOINTS PRINCIPALES
# ============================================================================

@app.post("/diagnostico", response_model=DiagnosticResponse, tags=["Diagnóstico"])
async def diagnosticar(request: DiagnosticRequest) -> DiagnosticResponse:
    """
    Diagnóstico completo de planta
    Entrada: Imagen base64 + sensores
    Salida: JSON estructurado con estado, confianza, síntomas, etc.
    """
    try:
        if not phi3_model or not await phi3_model.is_ready():
            raise HTTPException(status_code=503, detail="Modelo Phi-3.5 no disponible")
        
        logger.info(f"📥 Solicitud de diagnóstico para planta {request.plant_id or 'anónima'}")
        
        # Recuperar contexto RAG
        rag_query = f"síntomas estado planta {request.sensores.temp}°C humedad {request.sensores.humedad}%"
        rag_chunks = await rag_loader.retrieve_knowledge(rag_query, top_k=3)
        
        rag_context = "\n".join([
            f"- {chunk['metadata'].get('source', 'Unknown')}: {chunk['content'][:200]}..."
            for chunk in rag_chunks
        ]) if rag_chunks else "Sin contexto RAG disponible"
        
        logger.info(f"Recuperados {len(rag_chunks)} chunks de RAG")
        
        # Análisis con Phi-3.5
        logger.info("🧠 Ejecutando inferencia con Phi-3.5...")
        result = await phi3_model.analyze_plant(
            image_base64=request.imagen,
            sensores=request.sensores.dict(),
            rag_context=rag_context
        )
        
        if result["status"] != "success":
            raise HTTPException(status_code=500, detail=result.get("message"))
        
        diagnosis_data = result["data"]
        
        # Determinar si requiere acción humana
        confianza = float(diagnosis_data.get("confianza", 0.5))
        requiere_accion = confianza < 0.85 or diagnosis_data.get("estado") == "Peligro"
        
        # Crear respuesta
        diagnosis_id = str(uuid.uuid4())
        response = DiagnosticResponse(
            id=diagnosis_id,
            plant_id=request.plant_id,
            estado=diagnosis_data.get("estado", "Atención"),
            confianza=confianza,
            especie=diagnosis_data.get("especie", "Desconocida"),
            sintomas=diagnosis_data.get("sintomas", []),
            diagnostico=diagnosis_data.get("diagnostico", ""),
            recomendaciones=diagnosis_data.get("recomendaciones", []),
            fuentes=diagnosis_data.get("fuentes", []),
            requiere_accion_humana=requiere_accion,
            timestamp=datetime.now().isoformat()
        )
        
        # Persistir en DB (si está disponible)
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO diagnosticos (
                        id, plant_id, estado, confianza, especie, sintomas,
                        diagnostico, recomendaciones, fuentes, sensores
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    diagnosis_id,
                    request.plant_id,
                    response.estado,
                    response.confianza,
                    response.especie,
                    ",".join(response.sintomas),
                    response.diagnostico,
                    ",".join(response.recomendaciones),
                    ",".join(response.fuentes),
                    json.dumps(request.sensores.dict())
                ))
                conn.commit()
                cursor.close()
                conn.close()
                logger.info(f"✅ Diagnóstico guardado: {diagnosis_id}")
        except Exception as e:
            logger.warning(f"No se guardó en DB: {str(e)}")
        
        logger.info(f"✅ Diagnóstico completado: {response.estado} (confianza: {response.confianza:.2f})")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en diagnóstico: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/rag/upload", response_model=UploadResponse, tags=["Admin"])
async def upload_pdf(
    file: UploadFile = File(...),
    category: Optional[str] = None
) -> UploadResponse:
    """
    Endpoint para ADMIN: Inyectar PDFs dinámicamente al RAG
    Los PDFs se procesan, vectorizan y se agregan sin reiniciar
    """
    try:
        if not rag_loader:
            raise HTTPException(status_code=503, detail="RAG no inicializado")
        
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
        
        logger.info(f"📤 Admin subiendo PDF: {file.filename}")
        
        # Guardar PDF temporalmente
        upload_dir = "storage/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        pdf_path = os.path.join(upload_dir, file.filename)
        with open(pdf_path, "wb") as f:
            contents = await file.read()
            f.write(contents)
        
        # Procesar PDF
        result = await rag_loader.upload_pdf(
            pdf_path,
            metadata={"category": category or "general"}
        )
        
        if result["status"] == "success":
            logger.info(f"✅ PDF cargado: {file.filename} ({result['chunks']} chunks)")
            return UploadResponse(
                status="success",
                filename=file.filename,
                chunks=result["chunks"],
                message="PDF inyectado al RAG exitosamente"
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("message"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/rag/sources", tags=["Admin"])
async def get_rag_sources():
    """
    Endpoint para ADMIN: Listar PDFs cargados en RAG
    """
    try:
        if not rag_loader:
            raise HTTPException(status_code=503, detail="RAG no inicializado")
        
        sources = await rag_loader.get_sources()
        return {"sources": sources, "total": len(sources)}
        
    except Exception as e:
        logger.error(f"Error obteniendo sources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse, tags=["Sistema"])
async def health() -> HealthResponse:
    """
    Health check del sistema
    """
    try:
        model_ready = phi3_model and await phi3_model.is_ready()
        rag_ready = rag_loader is not None
        
        # Verificar DB
        db_ready = False
        try:
            conn = get_db_connection()
            if conn:
                conn.close()
                db_ready = True
        except:
            pass
        
        status = "healthy" if (model_ready and rag_ready) else "degraded"
        
        return HealthResponse(
            status=status,
            model_ready=model_ready,
            rag_ready=rag_ready,
            db_connected=db_ready,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error en health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint"""
    return {
        "name": "Mole AI v2.0",
        "version": "2.0.0",
        "model": "Phi-3.5 Vision-Instruct Q4",
        "endpoints": {
            "diagnostico": "POST /diagnostico",
            "admin_upload": "POST /admin/rag/upload",
            "admin_sources": "GET /admin/rag/sources",
            "health": "GET /health",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "mole_ai.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
