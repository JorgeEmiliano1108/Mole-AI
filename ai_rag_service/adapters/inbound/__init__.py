"""Adapter Inbound: FastAPI Router para RAG Service"""

import logging
import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, UploadFile, File

from ...domain.models import (
    VisionOutput, SensorData, DiagnoseRequest
)
from ...domain.exceptions import RAGServiceException
from ...use_cases import DiagnoseWithRAGUseCase, UploadPDFUseCase

logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMAS PYDANTIC
# ============================================================================

class SensorDataSchema(BaseModel):
    """Datos de sensores (Swagger)"""
    ph: float = Field(..., ge=0, le=14, description="pH del suelo")
    humedad: float = Field(..., ge=0, le=100, description="Humedad relativa %")
    temp: float = Field(..., ge=-50, le=60, description="Temperatura °C")
    uv: float = Field(..., ge=0, le=15, description="Radiación UV mW/cm²")


class VisionOutputSchema(BaseModel):
    """Output del servicio de visión (Swagger)"""
    estado: str = Field(..., description="Sana | Atención | Peligro")
    confianza: float = Field(..., ge=0, le=1, description="Confianza 0-1")
    especie_probable: str = Field(..., description="Especie identificada")
    sintomas: List[str] = Field(..., description="Síntomas detectados")
    análisis_visual: str = Field(..., description="Análisis visual detallado")


class DiagnoseRequestSchema(BaseModel):
    """Solicitud de diagnóstico (Swagger)"""
    vision_output: VisionOutputSchema = Field(..., description="Output de Vision Service")
    sensores: SensorDataSchema = Field(..., description="Datos de sensores")
    
    class Config:
        json_schema_extra = {
            "example": {
                "vision_output": {
                    "estado": "Atención",
                    "confianza": 0.85,
                    "especie_probable": "Solanum lycopersicum",
                    "sintomas": ["Manchas oscuras", "Defoliación"],
                    "análisis_visual": "Síntomas de tizón tardío"
                },
                "sensores": {
                    "ph": 6.5,
                    "humedad": 65.0,
                    "temp": 24.5,
                    "uv": 0.8
                }
            }
        }


class DiagnoseResponseSchema(BaseModel):
    """Respuesta de diagnóstico (Swagger)"""
    id: str = Field(..., description="ID único")
    timestamp: str = Field(..., description="Timestamp ISO")
    diagnostico: str = Field(..., description="Diagnóstico final")
    recomendaciones: List[str] = Field(..., description="Recomendaciones")
    fuentes_consultadas: List[str] = Field(..., description="PDFs consultados")
    confianza_final: float = Field(..., ge=0, le=1, description="Confianza final")
    requiere_accion_humana: bool = Field(..., description="¿Requiere intervención?")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "uuid-123",
                "timestamp": "2024-12-19T10:30:00",
                "diagnostico": "Planta con tizón tardío confirmado",
                "recomendaciones": ["Aplicar fungicida", "Mejorar ventilación"],
                "fuentes_consultadas": ["plant_diseases.pdf"],
                "confianza_final": 0.92,
                "requiere_accion_humana": False
            }
        }


class PDFUploadResponseSchema(BaseModel):
    """Response de PDF upload"""
    status: str
    message: str
    chunks: int


class SourceSchema(BaseModel):
    """Fuente cargada"""
    name: str
    chunks: int
    category: str


# ============================================================================
# FASTAPI ROUTER
# ============================================================================

def create_rag_router(
    diagnose_use_case: DiagnoseWithRAGUseCase,
    upload_use_case: UploadPDFUseCase,
    vector_store = None
) -> APIRouter:
    """Factory para crear router RAG"""
    router = APIRouter(prefix="/rag", tags=["RAG"])
    
    @router.post(
        "/diagnose",
        response_model=DiagnoseResponseSchema,
        summary="Diagnóstico final con RAG",
        description="Genera diagnóstico final integrando visión, sensores y conocimiento base"
    )
    async def diagnose_plant(request: DiagnoseRequestSchema) -> DiagnoseResponseSchema:
        """
        Endpoint principal de diagnóstico RAG
        
        - **vision_output**: Resultado del Vision Service
        - **sensores**: Datos de sensores ESP32
        
        Returns diagnóstico final con recomendaciones
        """
        try:
            diagnosis_id = str(uuid.uuid4())
            
            # Convertir a modelos del dominio
            vision_output = VisionOutput(
                estado=request.vision_output.estado,
                confianza=request.vision_output.confianza,
                especie_probable=request.vision_output.especie_probable,
                sintomas=request.vision_output.sintomas,
                análisis_visual=request.vision_output.análisis_visual
            )
            
            sensores = SensorData(
                ph=request.sensores.ph,
                humedad=request.sensores.humedad,
                temp=request.sensores.temp,
                uv=request.sensores.uv
            )
            
            domain_request = DiagnoseRequest(
                vision_output=vision_output,
                sensores=sensores
            )
            
            # Ejecutar use case
            logger.info(f"📥 Solicitud {diagnosis_id}")
            diagnosis = await diagnose_use_case.execute(domain_request)
            
            # Convertir resultado
            return DiagnoseResponseSchema(
                id=diagnosis_id,
                timestamp=datetime.now().isoformat(),
                diagnostico=diagnosis.diagnostico,
                recomendaciones=diagnosis.recomendaciones,
                fuentes_consultadas=diagnosis.fuentes_consultadas,
                confianza_final=diagnosis.confianza_final,
                requiere_accion_humana=diagnosis.requiere_accion_humana
            )
            
        except RAGServiceException as e:
            logger.error(f"❌ Error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"❌ Error inesperado: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post(
        "/admin/upload-pdf",
        response_model=PDFUploadResponseSchema,
        summary="Admin: Subir PDF a RAG",
        description="Inyecta dinámicamente un PDF al conocimiento base"
    )
    async def upload_pdf(file: UploadFile = File(...)) -> PDFUploadResponseSchema:
        """
        Endpoint admin para subir PDFs
        
        - **file**: Archivo PDF
        
        Returns número de chunks creados
        """
        try:
            if not file.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Solo archivos PDF")
            
            logger.info(f"📤 Subiendo: {file.filename}")
            
            # Leer PDF
            from PyPDF2 import PdfReader
            pdf_data = await file.read()
            
            # Extraer texto
            import io
            reader = PdfReader(io.BytesIO(pdf_data))
            documents = []
            for page in reader.pages:
                documents.append(page.extract_text())
            
            # Subir al vector store
            result = await upload_use_case.execute(
                documents,
                {"source": file.filename, "category": "uploaded"}
            )
            
            return PDFUploadResponseSchema(
                status="success",
                message=f"PDF {file.filename} inyectado",
                chunks=result["chunks"]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error en upload: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get(
        "/admin/sources",
        response_model=dict,
        summary="Admin: Listar fuentes",
        description="Lista PDFs cargados en RAG"
    )
    async def get_sources() -> dict:
        """Retorna fuentes cargadas"""
        try:
            if vector_store is None:
                return {"sources": [], "total": 0, "message": "Vector store no inicializado"}
            
            # Obtener metadata de fuentes
            sources_list = await vector_store.get_sources()
            
            return {
                "sources": sources_list,
                "total": len(sources_list),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Error en get_sources: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/health")
    async def health_check():
        """Health check"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    
    return router
