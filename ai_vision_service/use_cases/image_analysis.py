from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import json

from ..ports.input import ImageAnalyzerPort
from ..ports.output import ImageStoragePort, VisionRepositoryPort
from ..domain.models import ImageAnalysis, AnalysisType, PlantType, HealthStatus
from ..domain.exceptions import VisionException

class ImageAnalysisUseCase:
    """Caso de uso para análisis completo de imágenes de plantas con cache"""
    
    def __init__(
        self, 
        image_analyzer: ImageAnalyzerPort,
        storage: ImageStoragePort,
        repository: VisionRepositoryPort
    ):
        self.image_analyzer = image_analyzer
        self.storage = storage
        self.repository = repository
        # Cache en memoria para detecciones repetidas (TTL: 1 hora)
        self._analysis_cache = {}
        self._cache_ttl = timedelta(hours=1)
    
    async def execute(
        self, 
        image_b64: str, 
        analysis_type: AnalysisType,
        plant_context: str = ""
    ) -> ImageAnalysis:
        """Ejecuta análisis completo de imagen con cache"""
        try:
            # 1. Verificar cache primero
            cache_key = self._generate_cache_key(image_b64, analysis_type, plant_context)
            cached_analysis = self._get_cached_analysis(cache_key)
            if cached_analysis:
                # Agregar metadata de cache
                cached_analysis.from_cache = True
                return cached_analysis
            
            # 2. Análisis principal
            analysis = await self.image_analyzer.analyze_image_base64(image_b64, analysis_type)
            
            # 3. Detección adicional del tipo de planta si es desconocido
            current_plant_type_str = analysis.plant_type
            if current_plant_type_str == PlantType.DESCONOCIDA:
                detected_plant_type = await self.image_analyzer.detect_plant_type(image_b64)
                if detected_plant_type != PlantType.DESCONOCIDA:
                    # Mantener como string para consistencia con ImageAnalysis
                    analysis.plant_type = str(detected_plant_type)
                    current_plant_type_str = str(detected_plant_type)
                    analysis.confidence *= 0.9  # Reducir confianza un poco
            
            # 4. Detección de problemas de salud adicionales  
            health_issues = await self.image_analyzer.detect_health_issues(
                image_b64, 
                str(current_plant_type_str)
            )
            
            # Combinar detecciones
            if health_issues:
                analysis.detections.extend(health_issues)
                
                # Actualizar estado de salud si hay problemas adicionales
                if len(health_issues) > 1:
                    analysis.health_status = HealthStatus.MULTIPLE_ISSUES
                    analysis.confidence *= 0.8
                    analysis.recommendations.append(
                        "Múltiples problemas detectados - Priorizar tratamiento"
                    )
            
            # 5. Guardar en cache
            self._cache_analysis(cache_key, analysis)
            
            # 6. Guardar imagen y análisis
            image_bytes = self._decode_base64(image_b64)
            metadata = {
                "analysis_type": analysis.analysis_type,
                "plant_type": analysis.plant_type,
                "health_status": analysis.health_status,
                "plant_context": plant_context,
                "cached": False
            }
            
            await self.storage.save_image(analysis.image_id, image_bytes, metadata)
            await self.repository.save_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            raise VisionException(f"Error en análisis completo: {str(e)}")
    
    def _generate_cache_key(self, image_b64: str, analysis_type: AnalysisType, plant_context: str) -> str:
        """Genera clave única para cache basada en contenido"""
        # Usar hash de la imagen + tipo de análisis + contexto
        image_hash = hashlib.md5(image_b64.encode()).hexdigest()
        context_hash = hashlib.md5(plant_context.encode()).hexdigest()
        return f"{image_hash}_{analysis_type}_{context_hash}"
    
    def _get_cached_analysis(self, cache_key: str) -> Optional[ImageAnalysis]:
        """Obtiene análisis del cache si es válido"""
        if cache_key not in self._analysis_cache:
            return None
        
        cached_data = self._analysis_cache[cache_key]
        cached_time = cached_data["timestamp"]
        
        # Verificar TTL
        if datetime.now() - cached_time > self._cache_ttl:
            del self._analysis_cache[cache_key]
            return None
        
        return cached_data["analysis"]
    
    def _cache_analysis(self, cache_key: str, analysis: ImageAnalysis):
        """Guarda análisis en cache"""
        self._analysis_cache[cache_key] = {
            "analysis": analysis,
            "timestamp": datetime.now()
        }
        
        # Limpiar cache antiguo si es muy grande (máximo 100 entradas)
        if len(self._analysis_cache) > 100:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Limpia entradas antiguas del cache"""
        now = datetime.now()
        keys_to_delete = []
        
        for cache_key, cached_data in self._analysis_cache.items():
            if now - cached_data["timestamp"] > self._cache_ttl:
                keys_to_delete.append(cache_key)
        
        for key in keys_to_delete:
            del self._analysis_cache[key]
    
    async def get_analysis_history(self, image_id: str) -> Optional[ImageAnalysis]:
        """Recupera análisis anterior por ID"""
        try:
            return await self.repository.get_analysis(image_id)
        except Exception as e:
            raise VisionException(f"Error recuperando análisis: {str(e)}")
    
    async def find_similar_cases(
        self, 
        image_b64: str, 
        limit: int = 5
    ) -> list:
        """Encuentra casos similares para diagnóstico comparativo"""
        try:
            # Aquí implementaríamos búsqueda por similitud de vectores
            # Por ahora, búsqueda simple por metadatos
            image_bytes = self._decode_base64(image_b64)
            plant_type = await self.image_analyzer.detect_plant_type(image_b64)
            
            # Placeholder - implementar búsqueda vectorial real
            return await self.repository.search_similar_images([], limit)
            
        except Exception as e:
            raise VisionException(f"Error buscando casos similares: {str(e)}")
    
    def _decode_base64(self, image_b64: str) -> bytes:
        """Decodifica imagen base64"""
        import base64
        try:
            if ',' in image_b64:
                image_b64 = image_b64.split(',')[1]
            return base64.b64decode(image_b64)
        except Exception as e:
            raise VisionException(f"Error decodificando imagen: {str(e)}")

class PlantTypeDetectionUseCase:
    """Caso de uso especializado en detección de tipo de planta"""
    
    def __init__(self, image_analyzer: ImageAnalyzerPort):
        self.image_analyzer = image_analyzer
    
    async def execute(self, image_b64: str) -> Dict[str, Any]:
        """Detecta tipo de planta con confianza y contexto"""
        try:
            plant_type = await self.image_analyzer.detect_plant_type(image_b64)
            
            # Agregar información contextual basada en el tipo detectado
            context_info = self._get_plant_context(plant_type)
            
            return {
                "plant_type": plant_type,
                "confidence": 0.8,  # Placeholder
                "context": context_info,
                "detected_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise VisionException(f"Error en detección de planta: {str(e)}")
    
    def _get_plant_context(self, plant_type: PlantType) -> Dict[str, Any]:
        """Obtiene información contextual sobre el tipo de planta"""
        contexts = {
            PlantType.CHILE: {
                "common_name": "Chile mexicano",
                "care_tips": ["Requiere sol abundante", "Riego moderado", "Suelo bien drenado"],
                "common_issues": ["Pulgones", "Moho", "Deficiencia de calcio"]
            },
            PlantType.MAIZ: {
                "common_name": "Maíz",
                "care_tips": ["Espaciado adecuado", "Riego constante", "Fertilización nitrogenada"],
                "common_issues": ["Gusano de elote", "Roya", "Deficiencia de nitrógeno"]
            },
            PlantType.AGUACATE: {
                "common_name": "Aguacate",
                "care_tips": ["Suelo profundo", "Drenaje excelente", "Protección del viento"],
                "common_issues": ["Antracnosis", "Deficiencia de zinc", "Exceso de riego"]
            },
            PlantType.TOMATE: {
                "common_name": "Tomate",
                "care_tips": ["Tutorado", "Riego por goteo", "Poda regular"],
                "common_issues": ["Tizón tardío", "Mosca blanca", "Gusano cogollero"]
            },
            PlantType.ENDemICA_MEXICANA: {
                "common_name": "Planta endémica mexicana",
                "care_tips": ["Conservación prioritaria", "Condiciones naturales", "Mínima intervención"],
                "common_issues": ["Pérdida de hábitat", "Cambio climático", "Especies invasoras"]
            }
        }
        
        return contexts.get(str(plant_type), {
            "common_name": "Planta no identificada",
            "care_tips": ["Identificar especie", "Consultar experto", "Monitorear desarrollo"],
            "common_issues": ["Diagnóstico requerido"]
        })