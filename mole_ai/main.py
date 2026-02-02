from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import os
from dotenv import load_dotenv

from .domain.models.plant import (
    PlantDiagnosis, 
    SensorData, 
    PlantImage, 
    DiagnosticFilter,
    SystemMetrics
)
from .domain.exceptions import (
    PlantAnalysisException,
    ModelNotReadyError,
    ConfidenceThresholdError,
    ServiceUnavailableError
)
from .use_cases.unified_diagnostic import UnifiedDiagnosticUseCase
from .adapters.outbound.phi3_vision_adapter import Phi3VisionAdapter
from .adapters.outbound.unified_rag_adapter import UnifiedRAGAdapter
from .adapters.outbound.postgresql_adapter import PostgreSQLAdapter

load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dependencias globales (inyectadas)
vision_adapter: Optional[Phi3VisionAdapter] = None
rag_adapter: Optional[UnifiedRAGAdapter] = None
db_adapter: Optional[PostgreSQLAdapter] = None
diagnostic_use_case: Optional[UnifiedDiagnosticUseCase] = None


# Modelos Pydantic para API
class DiagnosticRequest(BaseModel):
    imagen: str  # base64
    sensores: Optional[SensorData] = None
    plant_id: Optional[str] = None
    force_rag_query: Optional[str] = None


class DiagnosticResponse(BaseModel):
    id: Optional[str] = None
    plant_id: Optional[str] = None
    estado: str
    confianza: float
    especie: Optional[str] = None
    sintomas: List[str] = []
    diagnostico: str
    recomendaciones: List[str] = []
    fuentes: List[str] = []
    modelo_utilizado: str
    tiempo_inferencia: Optional[float] = None
    requiere_accion_humana: bool
    created_at: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    model_ready: bool
    rag_ready: bool
    database_connected: bool
    system_metrics: Optional[Dict[str, Any]] = None


class VisionOnlyRequest(BaseModel):
    imagen: str
    context: Optional[str] = None


class KnowledgeRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 3


# Inyección de dependencias
async def get_vision_adapter() -> Phi3VisionAdapter:
    if vision_adapter is None:
        raise HTTPException(status_code=503, detail="Adaptador de visión no inicializado")
    return vision_adapter


async def get_rag_adapter() -> UnifiedRAGAdapter:
    if rag_adapter is None:
        raise HTTPException(status_code=503, detail="Adaptador RAG no inicializado")
    return rag_adapter


async def get_db_adapter() -> PostgreSQLAdapter:
    if db_adapter is None:
        raise HTTPException(status_code=503, detail="Adaptador de base de datos no inicializado")
    return db_adapter


async def get_diagnostic_use_case() -> UnifiedDiagnosticUseCase:
    if diagnostic_use_case is None:
        raise HTTPException(status_code=503, detail="Caso de uso de diagnóstico no inicializado")
    return diagnostic_use_case


# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización y limpieza de la aplicación FastAPI"""
    global vision_adapter, rag_adapter, db_adapter, diagnostic_use_case
    
    try:
        logger.info("🚀 Inicializando Mole AI con arquitectura hexagonal unificada...")
        
        # Inicializar adaptadores (infraestructura)
        logger.info("📦 Inicializando adaptadores de infraestructura...")
        
        db_adapter = PostgreSQLAdapter()
        await db_adapter.initialize()
        logger.info("✅ PostgreSQL Adapter inicializado")
        
        rag_adapter = UnifiedRAGAdapter()
        await rag_adapter.initialize()
        logger.info("✅ RAG Adapter inicializado")
        
        vision_adapter = Phi3VisionAdapter()
        await vision_adapter.initialize()
        logger.info("✅ Phi-3.5 Vision Adapter inicializado")
        
        # Inicializar caso de uso (lógica de negocio)
        logger.info("🎯 Inicializando casos de uso...")
        diagnostic_use_case = UnifiedDiagnosticUseCase(
            vision_provider=vision_adapter,
            knowledge_retriever=rag_adapter,
            sensor_data=db_adapter,
            persistence=db_adapter,
            model_manager=vision_adapter
        )
        logger.info("✅ Unified Diagnostic Use Case inicializado")
        
        logger.info("🎉 Mole AI v2.0 - Arquitectura Hexagonal Unificada ready!")
        yield
        
    except Exception as e:
        logger.error(f"❌ Error crítico en inicialización: {str(e)}")
        raise
    finally:
        # Limpieza de recursos
        logger.info("🔄 Realizando limpieza de recursos...")
        if db_adapter:
            await db_adapter.close()
        logger.info("✅ Recursos liberados")


# Crear aplicación FastAPI
app = FastAPI(
    title="Mole AI v2.0 - Diagnóstico de Plantas Endémicas Mexicanas",
    description="Sistema unificado con arquitectura hexagonal y Phi-3.5 Vision-Instruct Q4",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, configurar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Endpoints Principales
@app.post("/diagnostico", response_model=DiagnosticResponse, tags=["Diagnóstico"])
async def diagnosticar_planta(
    request: DiagnosticRequest,
    use_case: UnifiedDiagnosticUseCase = Depends(get_diagnostic_use_case)
):
    """
    Diagnóstico completo unificado de planta
    - Análisis visual con Phi-3.5
    - Recuperación de conocimiento RAG
    - Integración con sensores
    """
    try:
        logger.info(f"📥 Solicitud de diagnóstico para planta {request.plant_id or 'desconocida'}")
        
        # Crear imagen
        image = PlantImage(
            image_base64=request.imagen,
            plant_id=request.plant_id
        )
        
        # Ejecutar diagnóstico completo
        diagnosis = await use_case.execute_complete_diagnosis(
            image=image,
            sensor_input=request.sensores,
            plant_id=request.plant_id,
            force_rag_query=request.force_rag_query
        )
        
        # Convertir a respuesta API
        response = DiagnosticResponse(
            id=diagnosis.id,
            plant_id=diagnosis.plant_id,
            estado=diagnosis.estado.value,
            confianza=diagnosis.confianza,
            especie=diagnosis.especie,
            sintomas=diagnosis.sintomas,
            diagnostico=diagnosis.diagnostico,
            recomendaciones=diagnosis.recomendaciones,
            fuentes=diagnosis.fuentes,
            modelo_utilizado=diagnosis.modelo_utilizado,
            tiempo_inferencia=diagnosis.tiempo_inferencia,
            requiere_accion_humana=diagnosis.requiere_accion_humana,
            created_at=diagnosis.created_at.isoformat() if diagnosis.created_at else None
        )
        
        logger.info(f"✅ Diagnóstico completado: {diagnosis.estado} (confianza: {diagnosis.confianza:.2f})")
        return response
        
    except ModelNotReadyError as e:
        logger.error(f"❌ Modelo no listo: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Modelo Phi-3.5 no disponible: {str(e)}")
    except ConfidenceThresholdError as e:
        logger.error(f"❌ Confianza insuficiente: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Confianza insuficiente: {str(e)}")
    except PlantAnalysisException as e:
        logger.error(f"❌ Error en diagnóstico: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando diagnóstico: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.post("/vision/analizar", tags=["Análisis Visual"])
async def analizar_vision_solamente(
    request: VisionOnlyRequest,
    vision: Phi3VisionAdapter = Depends(get_vision_adapter)
):
    """Análisis visual rápido (sin RAG ni persistencia)"""
    try:
        image = PlantImage(image_base64=request.imagen)
        result = await vision.analyze_plant_image(image, request.context)
        return {"vision_result": result}
    except Exception as e:
        logger.error(f"Error en análisis visual: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error análisis visual: {str(e)}")


@app.post("/conocimiento/consultar", tags=["Conocimiento"])
async def consultar_conocimiento(
    request: KnowledgeRequest,
    rag: UnifiedRAGAdapter = Depends(get_rag_adapter)
):
    """Consulta directa a base de conocimiento RAG"""
    try:
        results = await rag.get_relevant_knowledge(
            query=request.query,
            filters=request.filters,
            top_k=request.top_k
        )
        return {"knowledge_results": results}
    except Exception as e:
        logger.error(f"Error en consulta RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error consulta conocimiento: {str(e)}")


# Endpoints de Datos
@app.get("/sensores/latest", tags=["Sensores"])
async def obtener_sensores_recientes(
    plant_id: Optional[str] = None,
    db: PostgreSQLAdapter = Depends(get_db_adapter)
):
    """Obtiene datos más recientes de sensores"""
    try:
        sensor_data = await db.get_latest_sensor_data(plant_id)
        return {"sensor_data": sensor_data.dict()}
    except Exception as e:
        logger.error(f"Error obteniendo sensores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sensores: {str(e)}")


@app.post("/sensores/guardar", tags=["Sensores"])
async def guardar_datos_sensores(
    sensor_data: SensorData,
    db: PostgreSQLAdapter = Depends(get_db_adapter)
):
    """Guarda nuevos datos de sensores"""
    try:
        success = await db.save_sensor_data(sensor_data)
        return {"success": success, "message": "Datos guardados correctamente"}
    except Exception as e:
        logger.error(f"Error guardando sensores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error guardando sensores: {str(e)}")


@app.get("/diagnosticos/historial/{plant_id}", tags=["Diagnóstico"])
async def obtener_historial_diagnosticos(
    plant_id: str,
    limit: int = 10,
    db: PostgreSQLAdapter = Depends(get_db_adapter)
):
    """Obtiene historial de diagnósticos de una planta"""
    try:
        diagnoses = await db.get_diagnosis_history(plant_id, limit)
        return {
            "plant_id": plant_id,
            "diagnoses": [d.dict() for d in diagnoses]
        }
    except Exception as e:
        logger.error(f"Error obteniendo historial: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error historial: {str(e)}")


# Endpoints de Sistema
@app.get("/health", response_model=HealthResponse, tags=["Sistema"])
async def health_check():
    """Health check completo del sistema"""
    try:
        # Verificar componentes
        model_ready = await vision_adapter.is_model_ready() if vision_adapter else False
        rag_ready = bool(rag_adapter and len(rag_adapter.documents) > 0) if rag_adapter else False
        db_connected = bool(db_adapter and db_adapter._connection and not db_adapter._connection.closed) if db_adapter else False
        
        # Obtener métricas si está disponible
        system_metrics = None
        if db_connected:
            try:
                system_metrics = await db_adapter.get_system_metrics()
            except:
                pass
        
        status = "healthy" if (model_ready and rag_ready and db_connected) else "unhealthy"
        
        return HealthResponse(
            status=status,
            service="Mole AI v2.0 - Hexagonal Architecture",
            version="2.0.0",
            model_ready=model_ready,
            rag_ready=rag_ready,
            database_connected=db_connected,
            system_metrics=system_metrics
        )
        
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Servicio no disponible: {str(e)}")


@app.get("/system/metrics", tags=["Sistema"])
async def obtener_metricas_sistema(
    db: PostgreSQLAdapter = Depends(get_db_adapter)
):
    """Obtiene métricas detalladas del sistema"""
    try:
        metrics = await db_adapter.get_system_metrics()
        
        # Agregar información de modelos
        if vision_adapter:
            model_info = await vision_adapter.get_model_info()
            metrics["model_info"] = model_info
        
        # Agregar información de RAG
        if rag_adapter:
            metrics["rag_info"] = {
                "total_documents": len(rag_adapter.documents),
                "vector_store_type": "chroma" if rag_adapter.use_chroma else "faiss",
                "embedding_model": rag_adapter.embedding_model
            }
        
        return {"metrics": metrics}
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error métricas: {str(e)}")


@app.get("/", tags=["Sistema"])
async def root():
    """Información general del servicio"""
    return {
        "service": "Mole AI v2.0",
        "architecture": "Hexagonal Modular",
        "model": "Phi-3.5 Vision-Instruct Q4",
        "version": "2.0.0",
        "description": "Sistema unificado de diagnóstico de plantas endémicas mexicanas",
        "endpoints": {
            "health": "/health",
            "diagnostico": "/diagnostico",
            "vision_analisis": "/vision/analizar",
            "conocimiento": "/conocimiento/consultar",
            "sensores": "/sensores/latest",
            "historial": "/diagnosticos/historial/{plant_id}",
            "metrics": "/system/metrics",
            "docs": "/docs"
        },
        "features": [
            "Arquitectura Hexagonal Pura",
            "Phi-3.5 Vision-Instruct Unificado",
            "RAG Integrado",
            "PostgreSQL Optimizado",
            "Inyección de Dependencias",
            "Error Handling Robusto"
        ]
    }


# Inicialización directa para desarrollo
if __name__ == "__main__":
    import uvicorn
    
    # Configuración para desarrollo
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )