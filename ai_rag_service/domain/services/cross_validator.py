"""Domain Services: Cross Validator para Validación Cruzada de Datos"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from domain.models import RAGChunk, VisionOutput, SensorData, DiagnoseRequest

logger = logging.getLogger(__name__)


class ValidationResult:
    """Resultado de validación cruzada"""
    
    def __init__(self):
        self.validation_score = 0.0
        self.confidence_adjustment = 0.0
        self.inconsistencies = []
        self.recommendations = []
        self.validation_factors = {}
        self.timestamp = datetime.now().isoformat()


class CrossValidator:
    """Validador cruzado para datos de visión, sensores y conocimiento RAG"""
    
    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
        
    def _initialize_validation_rules(self) -> Dict:
        """Inicializa reglas de validación basadas en botánica agrícola"""
        return {
            "ph_ranges": {
                "acidic": (0.0, 5.5),
                "optimal": (5.5, 7.0),
                "alkaline": (7.0, 8.5),
                "very_alkaline": (8.5, 14.0)
            },
            "humidity_ranges": {
                "dry": (0, 30),
                "optimal": (30, 70),
                "high": (70, 90),
                "very_high": (90, 100)
            },
            "temperature_ranges": {
                "cold": (0, 10),
                "cool": (10, 20),
                "optimal": (20, 30),
                "warm": (30, 35),
                "hot": (35, 45)
            },
            "disease_symptoms": {
                "fungal": ["manchas", "moho", "podredumbre", "marchitez", "clorosis"],
                "bacterial": ["manchas angulares", "pudrición blanda", "exudado", "cancro"],
                "viral": ["mosaico", "amarillamiento", "moteado", "deformación"],
                "nutritional": ["clorosis", "defoliación", "enanismo", "pudrición apical"],
                "environmental": ["quemadura", "scald", "necrosis"]
            }
        }
    
    def validate_diagnosis(self, 
                        vision_result: Optional[VisionOutput], 
                        rag_chunks: List[RAGChunk], 
                        sensor_data: Optional[SensorData],
                        query: str) -> ValidationResult:
        """
        Valida consistencia cruzada entre visión, sensores y RAG
        
        Args:
            vision_result: Resultado del análisis visual
            rag_chunks: Chunks recuperados del RAG
            sensor_data: Datos de sensores ambientales
            query: Query original del usuario
            
        Returns:
            ValidationResult con análisis completo
        """
        result = ValidationResult()
        
        try:
            logger.info(f"🔍 Iniciando validación cruzada para query: '{query[:50]}...'")
            
            # 1. Validación de Consistencia Internamente
            self._validate_internal_consistency(result, vision_result, rag_chunks, sensor_data)
            
            # 2. Validación de Sintomas vs Sensores
            if vision_result and sensor_data:
                self._validate_symptoms_vs_sensors(result, vision_result, sensor_data)
            
            # 3. Validación de RAG vs Contexto
            if rag_chunks and query:
                self._validate_rag_vs_context(result, rag_chunks, query, vision_result, sensor_data)
            
            # 4. Validación Agronómica
            if vision_result or sensor_data or rag_chunks:
                self._validate_agronomic_consistency(result, vision_result, rag_chunks, sensor_data)
            
            # 5. Calcular score final y ajustes
            self._calculate_final_validation_score(result)
            
            logger.info(f"✅ Validación cruzada completada - Score: {result.validation_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en validación cruzada: {str(e)}")
            result.inconsistencies.append(f"Validation error: {str(e)}")
            return result
    
    def _validate_internal_consistency(self, 
                                  result: ValidationResult,
                                  vision_result: Optional[VisionOutput],
                                  rag_chunks: List[RAGChunk], 
                                  sensor_data: Optional[SensorData]):
        """Valida consistencia interna de cada fuente de datos"""
        
        # Validar consistencia de datos visuales
        if vision_result:
            if vision_result.confidence < 0.0 or vision_result.confidence > 1.0:
                result.inconsistencies.append(
                    f"Confianza visual inválida: {vision_result.confidence} (debe estar 0-1)"
                )
                result.validation_score -= 0.1
            
            if not vision_result.tags:
                result.inconsistencies.append("Sin síntomas visuales reportados")
                result.validation_score -= 0.05
            
            # Validar especie vs síntomas
            disease_keywords = self.validation_rules["disease_symptoms"]
            symptoms_text = " ".join(vision_result.tags).lower()
            
            if "sano" in symptoms_text or "saludable" in symptoms_text:
                if len(vision_result.tags) > 0:
                    result.inconsistencies.append("Estado 'sano' con síntomas reportados")
                    result.validation_score -= 0.1
        
        # Validar consistencia de sensores
        if sensor_data:
            if sensor_data.ph_level < 0 or sensor_data.ph_level > 14:
                result.inconsistencies.append(
                    f"pH inválido: {sensor_data.ph_level} (debe estar 0-14)"
                )
                result.validation_score -= 0.05
            
            if sensor_data.humidity < 0 or sensor_data.humidity > 100:
                result.inconsistencies.append(
                    f"Humedad inválida: {sensor_data.humidity}% (debe estar 0-100%)"
                )
                result.validation_score -= 0.05
        
        # Validar chunks RAG
        if rag_chunks:
            for i, chunk in enumerate(rag_chunks):
                if chunk.score < 0.0 or chunk.score > 1.0:
                    result.inconsistencies.append(
                        f"Chunk {i+1} con confianza inválida: {chunk.score}"
                    )
                    result.validation_score -= 0.02
                
                if not chunk.content or len(chunk.content.strip()) < 10:
                    result.inconsistencies.append(
                        f"Chunk {i+1} con contenido vacío o muy corto"
                    )
                    result.validation_score -= 0.01
    
    def _validate_symptoms_vs_sensors(self, 
                                   result: ValidationResult,
                                   vision_result: VisionOutput, 
                                   sensor_data: SensorData):
        """Valida relación entre síntomas visuales y datos de sensores"""
        
        ph = sensor_data.ph_level
        humidity = sensor_data.humidity
        temperature = sensor_data.temperature
        symptoms = vision_result.tags
        
        symptoms_text = " ".join(symptoms).lower()
        
        # Regla 1: pH y síntomas fúngicos
        fungal_symptoms = self.validation_rules["disease_symptoms"]["fungal"]
        has_fungal = any(symptom in symptoms_text for symptom in fungal_symptoms)
        
        if has_fungal:
            ph_range = self.validation_rules["ph_ranges"]
            
            # pH ácido favorece hongos
            if ph < ph_range["acidic"][1]:  # pH < 5.5
                result.validation_factors["ph_fungal_acidic"] = True
                result.validation_score += 0.1
            else:
                result.validation_factors["ph_fungal_optimal"] = False
                result.validation_score -= 0.05
            
            # Alta humedad favorece hongos
            humidity_range = self.validation_rules["humidity_ranges"]
            if humidity > humidity_range["high"][0]:  # > 70%
                result.validation_factors["humidity_fungal_high"] = True
                result.validation_score += 0.1
            else:
                result.validation_factors["humidity_fungal_optimal"] = False
                result.validation_score -= 0.05
        
        # Regla 2: Clorosis y pH
        if "clorosis" in symptoms_text or "amarill" in symptoms_text:
            ph_range = self.validation_rules["ph_ranges"]
            
            # Clorosis puede ser por pH alcalino
            if ph > ph_range["alkaline"][0]:  # pH > 7.0
                result.validation_factors["ph_chlorosis_alkaline"] = True
                result.validation_score += 0.05
            else:
                result.validation_factors["ph_chlorosis_optimal"] = False
                result.validation_score -= 0.03
        
        # Regla 3: Marchitez y alta temperatura
        if "marchitez" in symptoms_text or "seca" in symptoms_text:
            temp_range = self.validation_rules["temperature_ranges"]
            
            if temperature > temp_range["warm"][0]:  # > 30°C
                result.validation_factors["temp_wilting_high"] = True
                result.validation_score += 0.05
            else:
                result.validation_factors["temp_wilting_optimal"] = False
                result.validation_score -= 0.03
        
        # Regla 4: Defoliación y condiciones ambientales
        if "defoliación" in symptoms_text or "caida" in symptoms_text:
            # Múltiples causas posibles, analizar combinación
            stress_factors = 0
            
            if temperature > 35:  # Estrés por calor
                result.validation_factors["temp_defoliation_heat_stress"] = True
                stress_factors += 1
            
            if humidity < 30:  # Estrés por sequía
                result.validation_factors["humidity_defoliation_drought_stress"] = True
                stress_factors += 1
            
            if ph < 5.5 or ph > 8.0:  # Estrés por pH
                result.validation_factors["ph_defoliation_stress"] = True
                stress_factors += 1
            
            if stress_factors >= 2:
                result.validation_score += 0.1
            elif stress_factors == 1:
                result.validation_score += 0.03
            else:
                result.validation_score -= 0.05
    
    def _validate_rag_vs_context(self, 
                               result: ValidationResult,
                               rag_chunks: List[RAGChunk], 
                               query: str,
                               vision_result: Optional[VisionOutput],
                               sensor_data: Optional[SensorData]):
        """Valida relevancia y calidad del contenido RAG recuperado"""
        
        if not rag_chunks:
            result.inconsistencies.append("No se recuperaron chunks RAG para validación")
            result.validation_score -= 0.1
            return
        
        query_lower = query.lower()
        
        # Validar calidad promedio de chunks
        avg_confidence = sum(chunk.score for chunk in rag_chunks) / len(rag_chunks)
        if avg_confidence < 0.3:
            result.inconsistencies.append("Baja calidad promedio de fuentes RAG")
            result.validation_score -= 0.1
        elif avg_confidence > 0.7:
            result.validation_factors["rag_high_quality"] = True
            result.validation_score += 0.05
        
        # Validar diversidad de fuentes
        source_types = set()
        for chunk in rag_chunks:
            source = chunk.metadata.get('source', '')
            if source.startswith("GBIF:"):
                source_types.add("GBIF")
            elif source.startswith("USDA:"):
                source_types.add("USDA")
            elif source.startswith("PDF:"):
                source_types.add("PDF")
            else:
                source_types.add("UNKNOWN")
        
        if len(source_types) >= 2:
            result.validation_factors["rag_multiple_sources"] = True
            result.validation_score += 0.05
        elif "UNKNOWN" in source_types:
            result.validation_factors["rag_unknown_sources"] = True
            result.validation_score -= 0.1
        
        # Validar relevancia del contenido
        relevant_chunks = 0
        for chunk in rag_chunks:
            content_lower = chunk.content.lower()
            
            # Buscar términos relevantes de la query
            query_terms = query_lower.split()
            content_matches = sum(1 for term in query_terms if term in content_lower)
            
            if content_matches > 0:
                relevant_chunks += 1
            elif any(plant_term in content_lower for plant_term in ["tomate", "papa", "solanum", "hortaliza"]):
                relevant_chunks += 0.5
        
        relevance_score = relevant_chunks / len(rag_chunks) if rag_chunks else 0
        result.validation_factors["rag_relevance_score"] = relevance_score
        
        if relevance_score > 0.7:
            result.validation_score += 0.1
        elif relevance_score < 0.3:
            result.validation_score -= 0.05
    
    def _validate_agronomic_consistency(self, 
                                     result: ValidationResult,
                                     vision_result: Optional[VisionOutput],
                                     rag_chunks: List[RAGChunk],
                                     sensor_data: Optional[SensorData]):
        """Valida consistencia agronómica general"""
        
        # Validar condiciones ambientales para cultivo
        if sensor_data:
            temp = sensor_data.temperature
            humidity = sensor_data.humidity
            
            # Validar combinación temperatura-humedad
            if temp > 30 and humidity > 80:
                # Alta temperatura + alta humedad = alto riesgo de enfermedades
                if vision_result:
                    symptoms = vision_result.tags
                    if not any(symptom.lower() in ["manchas", "moho", "podredumbre"] for symptom in symptoms):
                        result.inconsistencies.append(
                            "Condiciones de alto riesgo sin síntomas visuales típicos"
                        )
                        result.validation_score -= 0.05
            
            # Validar rangos óptimos
            temp_range = self.validation_rules["temperature_ranges"]
            humidity_range = self.validation_rules["humidity_ranges"]
            
            if temp_range["optimal"][0] <= temp <= temp_range["optimal"][1] and \
               humidity_range["optimal"][0] <= humidity <= humidity_range["optimal"][1]:
                result.validation_factors["optimal_conditions"] = True
                result.validation_score += 0.05
        
        # Validar推荐 vs conocimiento
        if rag_chunks:
            # Buscar recomendaciones prácticas en chunks
            practical_recommendations = 0
            for chunk in rag_chunks:
                content_lower = chunk.content.lower()
                if any(term in content_lower for term in ["fertilizar", "riego", "control", "preventivo", "monitoreo"]):
                    practical_recommendations += 1
            
            if practical_recommendations > 0:
                result.validation_factors["has_practical_recommendations"] = True
                result.validation_score += 0.03
    
    def _calculate_final_validation_score(self, result: ValidationResult):
        """Calcula score final de validación (0.0 - 1.0)"""
        
        # Normalizar score a rango 0-1
        result.validation_score = max(0.0, min(1.0, result.validation_score))
        
        # Calcular ajuste de confianza basado en validación
        if result.validation_score > 0.8:
            result.confidence_adjustment = 0.1  # Aumentar confianza
        elif result.validation_score > 0.6:
            result.confidence_adjustment = 0.05  # Pequeño aumento
        elif result.validation_score < 0.3:
            result.confidence_adjustment = -0.1  # Reducir confianza
        else:
            result.confidence_adjustment = 0.0  # Sin ajuste
        
        # Generar recomendaciones basadas en inconsistencias
        if result.inconsistencies:
            result.recommendations.extend([
                "Verificar manualmente los datos reportados",
                "Considerar análisis de laboratorio adicional",
                "Revisar calibración de sensores ambientales"
            ])
        
        if result.validation_score < 0.5:
            result.recommendations.extend([
                "Mejorar calidad de datos de entrada",
                "Incluir más contexto específico",
                "Validar con fuentes adicionales"
            ])
        
        if not result.recommendations:
            result.recommendations = ["Diagnóstico parece consistente y verificable"]
    
    def get_validation_summary(self, result: ValidationResult) -> Dict:
        """Genera resumen legible de validación"""
        return {
            "validation_score": result.validation_score,
            "confidence_adjustment": result.confidence_adjustment,
            "inconsistencies_count": len(result.inconsistencies),
            "recommendations_count": len(result.recommendations),
            "validation_factors": result.validation_factors,
            "inconsistencies": result.inconsistencies,
            "recommendations": result.recommendations,
            "timestamp": result.timestamp,
            "summary": self._generate_summary_text(result)
        }
    
    def _generate_summary_text(self, result: ValidationResult) -> str:
        """Genera texto de resumen interpretativo"""
        if result.validation_score >= 0.8:
            return f"Validación excelente: Alta consistencia y fiabilidad en los datos"
        elif result.validation_score >= 0.6:
            return f"Validación buena: Datos consistentes con algunas observaciones menores"
        elif result.validation_score >= 0.4:
            return f"Validación moderada: Datos con inconsistencias que requieren atención"
        else:
            return f"Validación pobre: Múltiples inconsistencias críticas detectadas"