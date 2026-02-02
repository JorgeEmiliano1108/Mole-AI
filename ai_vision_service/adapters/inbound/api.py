from typing import Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import base64
import io

from ...ports.input import ImageAnalyzerPort
from ...domain.models import ImageAnalysis, AnalysisType
from ...domain.exceptions import VisionException, UnsupportedImageFormat

class ImageAnalysisRequest(BaseModel):
    image_b64: str
    analysis_type: AnalysisType = AnalysisType.RGB
    plant_context: str = ""

class ImageAnalysisResponse(BaseModel):
    success: bool
    analysis: ImageAnalysis
    error_message: str = ""

class PlantDetectionResponse(BaseModel):
    success: bool
    plant_type: str
    confidence: float
    error_message: str = ""

class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str

router = APIRouter()

class VisionAPIController:
    def __init__(self, image_analyzer: ImageAnalyzerPort):
        self.image_analyzer = image_analyzer
    
    @router.post("/analyze", response_model=ImageAnalysisResponse)
    async def analyze_image(self, request: ImageAnalysisRequest):
        """Analiza una imagen y devuelve diagnóstico"""
        try:
            analysis = await self.image_analyzer.analyze_image_base64(
                request.image_b64, 
                request.analysis_type
            )
            
            return ImageAnalysisResponse(
                success=True,
                analysis=analysis
            )
            
        except UnsupportedImageFormat as e:
            raise HTTPException(status_code=400, detail=f"Formato de imagen inválido: {str(e)}")
        except VisionException as e:
            raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
    @router.post("/analyze/upload", response_model=ImageAnalysisResponse)
    async def analyze_uploaded_image(
        self,
        file: UploadFile = File(...),
        analysis_type: AnalysisType = Form(AnalysisType.RGB),
        plant_context: str = Form("")
    ):
        """Analiza imagen subida como archivo"""
        try:
            if not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")
            
            # Leer archivo y convertir a base64
            image_bytes = await file.read()
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            analysis = await self.image_analyzer.analyze_image_base64(
                image_b64, 
                analysis_type
            )
            
            return ImageAnalysisResponse(
                success=True,
                analysis=analysis
            )
            
        except UnsupportedImageFormat as e:
            raise HTTPException(status_code=400, detail=f"Formato de imagen inválido: {str(e)}")
        except VisionException as e:
            raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
    @router.post("/detect-plant", response_model=PlantDetectionResponse)
    async def detect_plant_type(self, request: ImageAnalysisRequest):
        """Detecta el tipo de planta en la imagen"""
        try:
            plant_type = await self.image_analyzer.detect_plant_type(request.image_b64)
            
            return PlantDetectionResponse(
                success=True,
                plant_type=plant_type,
                confidence=0.8  # Placeholder - implementar cálculo real
            )
            
        except VisionException as e:
            raise HTTPException(status_code=500, detail=f"Error en detección: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
    @router.get("/health", response_model=HealthCheckResponse)
    async def health_check():
        """Verificación de salud del servicio"""
        return HealthCheckResponse(
            status="healthy",
            service="Mole AI Vision Service",
            version="1.0.0"
        )

# Función factory para inyección de dependencias
def create_vision_controller(image_analyzer: ImageAnalyzerPort) -> VisionAPIController:
    return VisionAPIController(image_analyzer)