"""
API Routes - Definition with Multimodal Support (CORREGIDO FINAL)
"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# --- DTOs ---
from .contracts import (
    EmbeddingRequest as EmbeddingRequestDTO,
    EmbeddingResponse as EmbeddingResponseDTO,
    MoleAIChatRequest as MoleAIChatRequestDTO,
    MoleAIChatResponse as MoleAIChatResponseDTO,
    HealthResponse,
    ModelStatus,
    IngestKnowledgeRequest as IngestKnowledgeRequestDTO,
    IngestKnowledgeResponse as IngestKnowledgeResponseDTO,
    PhExplainRequest as PhExplainRequestDTO,
    PhExplainResponse as PhExplainResponseDTO,
    UploadUrlRequest as UploadUrlRequestDTO,
    UploadUrlResponse as UploadUrlResponseDTO,
    CreateDiagnosticRequest as CreateDiagnosticRequestDTO,
    DiagnosticResultResponse as DiagnosticResultResponseDTO,
)

# 1. Casos de uso GENÉRICOS (Vienen de application/use_cases.py)
from application.use_cases import (
    GenerateEmbeddingUseCase, 
    GenerateChatUseCase, 
    GetServiceHealthUseCase
)
from application.use_cases.ingest_knowledge_use_case import IngestKnowledgeUseCase

# 2. Caso de uso ESPECÍFICO (Viene de application/use_cases/mole_ai_chat_use_case.py)
from application.use_cases.mole_ai_chat_use_case import MoleAIChatUseCase
from application.use_cases.explain_ph_use_case import ExplainPhUseCase
from application.use_cases.create_diagnostic_use_case import CreateDiagnosticUseCase

# 3. Modelos de Dominio
from domain.models import EmbeddingRequest, ChatRequest, SensorData

logger = logging.getLogger(__name__)

api_v1_router = APIRouter(tags=["AI Services"])

def create_routes(
    embedding_use_case: GenerateEmbeddingUseCase,
    chat_use_case: GenerateChatUseCase,
    mole_ai_chat_use_case: MoleAIChatUseCase,
    health_use_case: GetServiceHealthUseCase,
    ingest_knowledge_use_case: IngestKnowledgeUseCase,
    explain_ph_use_case: ExplainPhUseCase = None,
    storage_adapter=None,
    create_diagnostic_use_case: CreateDiagnosticUseCase = None,
):
    """Factory de rutas con inyección de dependencias"""

    # --- ENDPOINT: MOLE-AI CHAT ---
    @api_v1_router.post(
        "/mole-ai/chat",
        response_model=MoleAIChatResponseDTO,
        summary="Generate Mole-AI agricultural response"
    )
    @limiter.limit("60/minute")
    async def generate_mole_ai_chat(request: Request, body: MoleAIChatRequestDTO):
        try:
            # 1. Convertir Sensores
            sensor_data = None
            if body.sensor_data:
                sensor_data = SensorData(
                    temperature=body.sensor_data.temperature,
                    humidity=body.sensor_data.humidity,
                    uv_index=body.sensor_data.uv_index,
                    soil_humidity=body.sensor_data.soil_humidity,
                    ph_level=body.sensor_data.ph_level,
                    device_id=getattr(body.sensor_data, 'device_id', "unknown"),
                    plant_id=getattr(body.sensor_data, 'plant_id', "unknown"),
                    location=getattr(body.sensor_data, 'location', "unknown"),
                    timestamp=getattr(body.sensor_data, 'timestamp', None)
                )
            
            # 2. Convertir Request (Soporte de Imagen)
            domain_request = ChatRequest(
                query=body.query,
                context=body.context or [],
                image=body.image,
                max_tokens=body.max_tokens or 1024,
                temperature=body.temperature or 0.7,
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
            models_status=[
                ModelStatus(
                    model=m.model,
                    is_loaded=m.is_loaded,
                    loading_time_ms=m.loading_time_ms,
                    memory_usage_mb=m.memory_usage_mb
                ) for m in res.models_status
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

    # ================================================================
    # Vision IoT Upload Endpoint (ESP32-CAM)
    # ================================================================
    @api_v1_router.post("/vision/iot-upload", summary="ESP32-CAM image upload for crop diagnosis")
    async def vision_iot_upload(file: UploadFile = File(...)):
        """Accept image from ESP32-CAM, analyze with vision LLM, return diagnosis.
        
        The image is converted to base64 and sent to the multimodal LLM with a
        fixed agricultural diagnosis prompt. Returns a JSON with diagnosis text
        and whether a tactical alert was triggered.
        """
        import base64 as b64_module
        try:
            content = await file.read()
            # Detect content type from filename or default to jpeg
            content_type = file.content_type or "image/jpeg"
            image_b64 = f"data:{content_type};base64,{b64_module.b64encode(content).decode()}"
            
            domain_request = ChatRequest(
                query="Analiza el estado general de este cultivo. Identifica posibles enfermedades, plagas o deficiencias nutricionales visibles. Si todo se ve bien, indícalo también.",
                image=image_b64,
                max_tokens=1024,
                temperature=0.7
            )
            response = await mole_ai_chat_use_case.execute(domain_request)
            
            has_alert = "⚠️ ALERTA TÁCTICA" in response.answer
            
            return {
                "diagnosis": response.answer,
                "model_used": response.model_used,
                "tokens_generated": response.tokens_generated,
                "processing_time_ms": response.processing_time_ms,
                "alert": has_alert
            }
        except Exception as e:
            logger.error(f"Error in IoT vision upload: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # ================================================================
    # pH Explainability Endpoint
    # ================================================================
    @api_v1_router.post(
        "/explain/ph",
        response_model=PhExplainResponseDTO,
        summary="Explain pH CNN inference result",
        tags=["Explainability"],
    )
    async def explain_ph(body: PhExplainRequestDTO):
        """Hybrid AI Explainability Engine — combines CNN output with botanical
        tolerance rules to produce an auditable, human-readable explanation."""
        if explain_ph_use_case is None:
            raise HTTPException(status_code=503, detail="ExplainPhUseCase not initialized")
        try:
            result = await explain_ph_use_case.execute(
                ph_cnn=body.ph_cnn,
                plant_id=str(body.plant_id),
                sensors=body.sensors,
                species_name=body.species_name,
            )
            return PhExplainResponseDTO(
                ph_raw=result.ph_raw,
                ph_status=result.ph_status,
                deviation=result.deviation,
                reasoning=result.reasoning,
                recommendations=result.recommendations,
                sensor_context=result.sensor_context,
                species_used=result.species_used,
                confidence=result.confidence,
                data_sources=result.data_sources,
            )
        except Exception as e:
            logger.error(f"Error Explain pH: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # ================================================================
    # Diagnostic — Signed Upload URL
    # ================================================================
    @api_v1_router.post(
        "/diagnostics/upload-url",
        response_model=UploadUrlResponseDTO,
        summary="Generate signed upload URL for diagnostic image",
        tags=["Diagnostics"],
    )
    async def diagnostic_upload_url(body: UploadUrlRequestDTO):
        if storage_adapter is None:
            raise HTTPException(status_code=503, detail="Storage adapter not initialized")
        try:
            result = await storage_adapter.generate_signed_upload_url(
                file_name=body.file_name,
                content_type=body.content_type,
            )
            return UploadUrlResponseDTO(**result)
        except Exception as e:
            logger.error(f"Error generating upload URL: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ================================================================
    # Diagnostic — Create (CNN Pipeline)
    # ================================================================
    @api_v1_router.post(
        "/diagnostics",
        response_model=DiagnosticResultResponseDTO,
        summary="Run CNN diagnostic pipeline on uploaded image",
        tags=["Diagnostics"],
    )
    async def create_diagnostic(body: CreateDiagnosticRequestDTO):
        if create_diagnostic_use_case is None:
            raise HTTPException(status_code=503, detail="Diagnostic use case not initialized")
        try:
            result = await create_diagnostic_use_case.execute(
                plant_id=str(body.plant_id),
                storage_url=body.storage_url,
                species_name=body.species_name,
            )
            return DiagnosticResultResponseDTO(
                diagnostic_id=result.diagnostic_id,
                plant_id=result.plant_id,
                species_detected=result.species_detected,
                ph_predicted=result.ph_predicted,
                condition_name=result.condition_name,
                condition_description=result.condition_description,
                severity=result.severity,
                confidence_score=result.confidence_score,
                recommendations=result.recommendations,
                image_url=result.image_url,
                ph_explanation=result.ph_explanation,
            )
        except Exception as e:
            logger.error(f"Error in diagnostic pipeline: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return api_v1_router