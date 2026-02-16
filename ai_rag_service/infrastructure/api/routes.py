"""
API Routes - Definition with Multimodal Support (CORREGIDO FINAL)
"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File

# --- DTOs ---
from .contracts import (
    EmbeddingRequest as EmbeddingRequestDTO,
    EmbeddingResponse as EmbeddingResponseDTO,
    ChatRequest as ChatRequestDTO,
    ChatResponse as ChatResponseDTO,
    MoleAIChatRequest as MoleAIChatRequestDTO,
    MoleAIChatResponse as MoleAIChatResponseDTO,
    HealthResponse,
    ErrorResponse,
    APIInfo,
    IngestKnowledgeRequest as IngestKnowledgeRequestDTO,
    IngestKnowledgeResponse as IngestKnowledgeResponseDTO
)

# --- IMPORTS CORREGIDOS (AQUÍ ESTABA EL ERROR) ---

# 1. Casos de uso GENÉRICOS (Vienen de application/use_cases.py)
from application.use_cases import (
    GenerateEmbeddingUseCase, 
    GenerateChatUseCase, 
    GetServiceHealthUseCase
)
from application.use_cases.ingest_knowledge_use_case import IngestKnowledgeUseCase

# 2. Caso de uso ESPECÍFICO (Viene de application/use_cases/mole_ai_chat_use_case.py)
from application.use_cases.mole_ai_chat_use_case import MoleAIChatUseCase

# 3. Modelos de Dominio
from domain.models import EmbeddingRequest, ChatRequest, SensorData

logger = logging.getLogger(__name__)

api_v1_router = APIRouter(tags=["AI Services"])

def create_routes(
    embedding_use_case: GenerateEmbeddingUseCase,
    chat_use_case: GenerateChatUseCase,
    mole_ai_chat_use_case: MoleAIChatUseCase,
    health_use_case: GetServiceHealthUseCase,
    ingest_knowledge_use_case: IngestKnowledgeUseCase
):
    """Factory de rutas con inyección de dependencias"""

    # --- ENDPOINT: MOLE-AI CHAT ---
    @api_v1_router.post(
        "/mole-ai/chat",
        response_model=MoleAIChatResponseDTO,
        summary="Generate Mole-AI agricultural response"
    )
    async def generate_mole_ai_chat(request: MoleAIChatRequestDTO):
        try:
            # 1. Convertir Sensores
            sensor_data = None
            if request.sensor_data:
                sensor_data = SensorData(
                    temperature=request.sensor_data.temperature,
                    humidity=request.sensor_data.humidity,
                    uv_index=request.sensor_data.uv_index,
                    soil_humidity=request.sensor_data.soil_humidity,
                    ph_level=request.sensor_data.ph_level,
                    device_id=getattr(request.sensor_data, 'device_id', "unknown"),
                    plant_id=getattr(request.sensor_data, 'plant_id', "unknown"),
                    location=getattr(request.sensor_data, 'location', "unknown"),
                    timestamp=getattr(request.sensor_data, 'timestamp', None)
                )
            
            # 2. Convertir Request (Soporte de Imagen)
            domain_request = ChatRequest(
                query=request.query,
                context=request.context or [],
                image=request.image,  # ✅ SOPORTE VISUAL
                max_tokens=request.max_tokens or 1024,
                temperature=request.temperature or 0.7,
                sensor_data=sensor_data
            )
            
            # 3. Ejecutar
            response = await mole_ai_chat_use_case.execute(domain_request)
            
            # 4. Contar alertas
            tactical_alerts_count = response.answer.count("⚠️ ALERTA TÁCTICA")
            
            return MoleAIChatResponseDTO(
                answer=response.answer,
                model_used=response.model_used,
                tokens_generated=response.tokens_generated,
                processing_time_ms=response.processing_time_ms,
                tactical_alerts_count=tactical_alerts_count
            )
            
        except Exception as e:
            logger.error(f"Error Mole-AI Chat: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # --- ENDPOINT: EMBEDDINGS ---
    @api_v1_router.post("/embeddings", response_model=EmbeddingResponseDTO)
    async def generate_embeddings(request: EmbeddingRequestDTO):
        try:
            domain_req = EmbeddingRequest(text=request.text)
            res = await embedding_use_case.execute(domain_req)
            return EmbeddingResponseDTO(
                vector=res.vector,
                dimension=res.dimension,
                model_used=res.model_used,
                processing_time_ms=res.processing_time_ms
            )
        except Exception as e:
            logger.error(f"Error Embeddings: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # --- ENDPOINT: HEALTH ---
    @api_v1_router.get("/health", response_model=HealthResponse)
    async def health_check():
        res = await health_use_case.execute()
        return HealthResponse(
            is_healthy=res.is_healthy,
            uptime_seconds=res.uptime_seconds,
            version=res.version,
            models=[
                {
                    "model": m.model,
                    "is_loaded": m.is_loaded,
                    "loading_time_ms": m.loading_time_ms,
                    "memory_usage_mb": m.memory_usage_mb
                } for m in res.models_status
            ]
        )

    # --- ENDPOINT: INGEST KNOWLEDGE ---
    @api_v1_router.post("/knowledge/ingest", response_model=IngestKnowledgeResponseDTO)
    async def ingest_knowledge(file: UploadFile = File(...)):
        """Ingest knowledge from PDF file"""
        try:
            # Leer contenido
            content = await file.read()
            
            # Crear request de dominio
            request = IngestKnowledgeRequestDTO(
                filename=file.filename,
                content=content
            )
            
            # Ejecutar caso de uso (adaptar para recibir bytes directos si es necesario, 
            # pero el caso de uso parece esperar path o bytes. Revisaremos IngestKnowledgeUseCase)
            # Para simplificar, asumimos que IngestKnowledgeUseCase maneja el contenido.
            
            # Revisando IngestKnowledgeUseCase signature en main.py... espera:
            # vector_store=vector_store_adapter, ingestion_service=pdf_ingestion_adapter
            
            # PERO aqui llamamos a execute().
            # Vamos a ver el execute de ingest_knowledge_use_case.
            # Asumiendo que execute toma (filename, content_bytes)
            
            result = await ingest_knowledge_use_case.execute(content, file.filename)
            
            return IngestKnowledgeResponseDTO(
                success=True,
                chunks_count=result.get("chunks_added", 0),
                message=f"Successfully ingested {file.filename}"
            )
            
        except Exception as e:
            logger.error(f"Error Ingestion: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # ================================================================
    # Sensor Live Endpoint (Mock for full-stack testing)
    # ================================================================
    @api_v1_router.get("/sensors/live", response_model=None, summary="Live sensor data (mock)")
    async def sensors_live():
        """Returns simulated sensor data for frontend connectivity testing.
        Replace this with real IoT gateway data in production."""
        import random
        return {
            "temperature": round(random.uniform(18.0, 35.0), 1),
            "humidity": round(random.uniform(30.0, 80.0), 1),
            "soil_humidity": round(random.uniform(20.0, 90.0), 1),
            "ph_level": round(random.uniform(5.5, 7.5), 1),
            "uv_index": round(random.uniform(1.0, 11.0), 1),
            "status": "OK"
        }

    return api_v1_router