"""Adapter Inbound: FastAPI Router para Vision Service"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from datetime import datetime

from ...domain.models import VisionAnalysisRequest as DomainRequest
from ...domain.exceptions import VisionServiceException
from ...use_cases import AnalyzePlantVisionUseCase

logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMAS PYDANTIC (Swagger)
# ============================================================================

class PlantSymptomSchema(BaseModel):
    """Síntoma de planta (Swagger)"""
    nombre: str = Field(..., description="Nombre del síntoma")
    confianza: float = Field(..., ge=0, le=1, description="Confianza 0-1")
    descripcion: str = Field(..., description="Descripción del síntoma")


class VisionAnalyzeRequestSchema(BaseModel):
    """Solicitud de análisis visual (Swagger)"""
    image_base64: str = Field(..., description="Imagen en base64")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            }
        }


class VisionAnalyzeResponseSchema(BaseModel):
    """Respuesta de análisis visual (Swagger)"""
    id: str = Field(..., description="ID único de análisis")
    timestamp: str = Field(..., description="Timestamp ISO 8601")
    estado: str = Field(..., description="Sana | Atención | Peligro")
    confianza: float = Field(..., ge=0, le=1, description="Confianza del análisis")
    sintomas: list[PlantSymptomSchema] = Field(..., description="Síntomas detectados")
    especie_probable: str = Field(..., description="Especie probable")
    análisis_visual: str = Field(..., description="Análisis visual detallado")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "uuid-123",
                "timestamp": "2024-12-19T10:30:00",
                "estado": "Atención",
                "confianza": 0.85,
                "sintomas": [
                    {
                        "nombre": "Manchas oscuras",
                        "confianza": 0.9,
                        "descripcion": "Manchas necróticas en hojas"
                    }
                ],
                "especie_probable": "Solanum lycopersicum",
                "análisis_visual": "Planta con síntomas de enfermedad fúngica"
            }
        }


class HealthResponseSchema(BaseModel):
    """Estado de salud (Swagger)"""
    status: str
    model_ready: bool
    timestamp: str


# ============================================================================
# FASTAPI ROUTER
# ============================================================================

def create_vision_router(use_case: AnalyzePlantVisionUseCase) -> APIRouter:
    """Factory para crear router de visión"""
    router = APIRouter(prefix="/vision", tags=["Vision"])
    
    @router.post(
        "/analyze",
        response_model=VisionAnalyzeResponseSchema,
        summary="Analizar imagen de planta",
        description="Analiza una imagen de planta y retorna diagnóstico visual estructurado"
    )
    async def analyze_plant(request: VisionAnalyzeRequestSchema) -> VisionAnalyzeResponseSchema:
        """
        Endpoint principal de análisis visual
        
        - **image_base64**: Imagen codificada en base64
        
        Returns:
        - **estado**: Sana, Atención o Peligro
        - **confianza**: 0.0-1.0
        - **sintomas**: Lista de síntomas detectados
        - **especie_probable**: Especie identificada
        """
        try:
            import uuid
            analysis_id = str(uuid.uuid4())
            
            # Crear request del dominio
            domain_request = DomainRequest(image_base64=request.image_base64)
            
            # Ejecutar use case
            logger.info(f"📥 Recibida solicitud {analysis_id}")
            result = await use_case.execute(domain_request)
            
            # Convertir resultado
            return VisionAnalyzeResponseSchema(
                id=analysis_id,
                timestamp=datetime.now().isoformat(),
                estado=result.estado.value,
                confianza=result.confianza,
                sintomas=[
                    PlantSymptomSchema(
                        nombre=s.nombre,
                        confianza=s.confianza,
                        descripcion=s.descripcion
                    )
                    for s in result.sintomas
                ],
                especie_probable=result.especie_probable,
                análisis_visual=result.análisis_visual
            )
            
        except VisionServiceException as e:
            logger.error(f"❌ Error de negocio: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"❌ Error inesperado: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
    @router.get(
        "/health",
        response_model=HealthResponseSchema,
        summary="Health check",
        description="Verifica estado del servicio"
    )
    async def health_check(use_case=use_case) -> HealthResponseSchema:
        """Health check del servicio"""
        try:
            model_ready = await use_case.vision_model.is_ready()
            return HealthResponseSchema(
                status="healthy" if model_ready else "degraded",
                model_ready=model_ready,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return HealthResponseSchema(
                status="unhealthy",
                model_ready=False,
                timestamp=datetime.now().isoformat()
            )
    
    return router
