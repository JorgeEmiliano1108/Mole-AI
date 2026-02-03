"""Use case: Analizar imagen de planta"""

import logging
from ..domain.models import VisionAnalysisRequest, VisionAnalysisResult
from ..domain.ports import VisionModelPort
from ..domain.exceptions import ModelNotReadyException, AnalysisFailedException

logger = logging.getLogger(__name__)


class AnalyzePlantVisionUseCase:
    """Use case para análisis visual de plantas"""
    
    def __init__(self, vision_model: VisionModelPort):
        self.vision_model = vision_model
    
    async def execute(self, request: VisionAnalysisRequest) -> VisionAnalysisResult:
        """
        Ejecuta análisis visual de planta
        
        Args:
            request: VisionAnalysisRequest con imagen en base64
            
        Returns:
            VisionAnalysisResult con estado, confianza, síntomas, etc.
            
        Raises:
            ModelNotReadyException: Si el modelo no está disponible
            AnalysisFailedException: Si el análisis falla
        """
        logger.info("Iniciando análisis visual...")
        
        # Verificar que modelo esté listo
        if not await self.vision_model.is_ready():
            logger.error("Modelo Phi-3.5 no está listo")
            raise ModelNotReadyException("Phi-3.5 Vision no está inicializado")
        
        try:
            # Ejecutar análisis
            result = await self.vision_model.analyze_image(request)
            logger.info(f"✅ Análisis completado: {result.estado}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Análisis falló: {str(e)}")
            raise AnalysisFailedException(f"Error en análisis visual: {str(e)}")
