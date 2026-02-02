from typing import Dict, Any, Optional, List
from datetime import datetime

from ...ports.input import DiagnosticPort, KnowledgeBasePort
from ...ports.output import DataPersistencePort
from ...domain.models import SensorData, PlantDiagnosis, LLMResponse
from ...domain.prompts import MoleAIPrompts
from ...domain.exceptions import DiagnosticError, InsufficientContextError

class PlantDiagnosticUseCase:
    """Caso de uso principal para diagnóstico de plantas con RAG"""
    
    def __init__(
        self,
        llm_provider,
        knowledge_base: KnowledgeBasePort,
        persistence: DataPersistencePort
    ):
        self.llm_provider = llm_provider
        self.knowledge_base = knowledge_base
        self.persistence = persistence
        
    async def diagnose_plant(
        self, 
        sensor_data: Dict[str, Any], 
        vision_results: Optional[Dict[str, Any]] = None,
        plant_context: str = ""
    ) -> Dict[str, Any]:
        """Realiza diagnóstico completo basado en datos y contexto RAG"""
        try:
            # 1. Validar datos de entrada
            validated_sensor_data = self._validate_sensor_data(sensor_data)
            
            # 2. Buscar contexto relevante en la base de conocimiento
            rag_context = await self._search_knowledge_context(
                validated_sensor_data, 
                vision_results
            )
            
            # 3. Generar prompt especializado
            diagnostic_prompt = self._build_diagnostic_prompt(
                validated_sensor_data,
                vision_results,
                rag_context,
                plant_context
            )
            
            # 4. Obtener diagnóstico del LLM
            llm_response = await self.llm_provider.generate_response(
                prompt=diagnostic_prompt,
                context=rag_context
            )
            
            # 5. Procesar respuesta y crear diagnóstico
            diagnosis = self._process_llm_response(
                llm_response,
                validated_sensor_data,
                vision_results,
                rag_context
            )
            
            # 6. Guardar diagnóstico
            await self.persistence.save_diagnosis(diagnosis.to_dict())
            
            return diagnosis.to_dict()
            
        except Exception as e:
            raise DiagnosticError(f"Error en diagnóstico: {str(e)}")
    
    async def _search_knowledge_context(
        self, 
        sensor_data: SensorData, 
        vision_results: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Busca contexto relevante en la base de conocimiento"""
        context_parts = []
        
        try:
            # Construir query basada en problemas detectados
            query_parts = []
            
            # Análisis de sensores
            if sensor_data.humidity < 30:
                query_parts.append("baja humedad ambiental plantas mexicanas")
            elif sensor_data.soil_moisture < 40:
                query_parts.append("estrés hídrico suelo seco")
            
            if sensor_data.ph < 6.0:
                query_parts.append("suelo ácido plantas méxicas")
            elif sensor_data.ph > 7.5:
                query_parts.append("suelo alcalino agricultura")
            
            if sensor_data.temperature > 35:
                query_parts.append("estrés por calor plantas")
            elif sensor_data.temperature < 10:
                query_parts.append("daño por frío plantas")
            
            # Análisis de visión
            if vision_results:
                health_status = vision_results.get("health_status", "")
                if "stress" in health_status.lower():
                    query_parts.append("estrés hídrico tratamiento")
                elif "pest" in health_status.lower():
                    query_parts.append("control plagas orgánico mexicano")
                elif "deficiency" in health_status.lower():
                    query_parts.append("deficiencia nutricional plantas")
            
            # Buscar en base de conocimiento
            if query_parts:
                for query_part in query_parts:
                    results = await self.knowledge_base.search_knowledge(query_part, limit=2)
                    context_parts.extend([result["content"] for result in results])
            
            return context_parts[:settings.RAG_TOP_K]  # Limitar cantidad de contexto
            
        except Exception as e:
            print(f"Error buscando contexto: {str(e)}")
            return []
    
    def _build_diagnostic_prompt(
        self,
        sensor_data: SensorData,
        vision_results: Optional[Dict[str, Any]],
        rag_context: List[str],
        plant_context: str
    ) -> str:
        """Construye prompt para diagnóstico"""
        if vision_results:
            # Prompt integrado con visión
            prompt = MoleAIPrompts.get_vision_diagnosis_prompt(
                vision_results,
                sensor_data.to_dict(),
                "\n---\n".join(rag_context)
            )
        else:
            # Prompt solo con sensores
            prompt = MoleAIPrompts.get_sensor_analysis_prompt(
                sensor_data.to_dict(),
                "\n---\n".join(rag_context)
            )
        
        # Agregar contexto adicional si se proporciona
        if plant_context:
            prompt += f"\n\nCONTEXTO ADICIONAL DEL USUARIO:\n{plant_context}"
        
        return prompt
    
    def _validate_sensor_data(self, sensor_data: Dict[str, Any]) -> SensorData:
        """Valida y convierte datos de sensores"""
        try:
            return SensorData(
                device_id=sensor_data.get("device_id", "unknown"),
                timestamp=datetime.fromisoformat(
                    sensor_data.get("timestamp", datetime.now().isoformat())
                ),
                humidity=float(sensor_data.get("humidity", 0)),
                temperature=float(sensor_data.get("temperature", 0)),
                ph=float(sensor_data.get("ph", 0)),
                uv_index=float(sensor_data.get("uv_index", 0)),
                soil_moisture=float(sensor_data.get("soil_moisture", 0)),
                plant_id=sensor_data.get("plant_id")
            )
        except Exception as e:
            raise InvalidSensorDataError(f"Datos de sensores inválidos: {str(e)}")
    
    def _process_llm_response(
        self,
        llm_response: Dict[str, Any],
        sensor_data: SensorData,
        vision_results: Optional[Dict[str, Any]],
        rag_context: List[str]
    ) -> PlantDiagnosis:
        """Procesa respuesta del LLM y crea objeto de diagnóstico"""
        content = llm_response.get("content", "")
        
        # Extraer información estructurada de la respuesta
        diagnosis_text = self._extract_diagnosis_text(content)
        urgency_level = self._extract_urgency_level(content)
        treatment_plan = self._extract_treatment_plan(content)
        recommendations = self._extract_recommendations(content)
        
        # Determinar confianza basada en contexto disponible
        confidence = self._calculate_confidence(
            sensor_data, vision_results, rag_context, llm_response
        )
        
        return PlantDiagnosis(
            plant_id=sensor_data.plant_id,
            sensor_data=sensor_data,
            vision_analysis=vision_results,
            rag_context=rag_context,
            diagnosis=diagnosis_text,
            treatment_plan=treatment_plan,
            urgency_level=urgency_level,
            confidence=confidence,
            recommendations=recommendations
        )
    
    def _extract_diagnosis_text(self, content: str) -> str:
        """Extrae texto principal del diagnóstico"""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('DIAGNÓSTICO:'):
                return line.replace('DIAGNÓSTICO:', '').strip()
        return content.strip()
    
    def _extract_urgency_level(self, content: str) -> str:
        """Extrae nivel de urgencia"""
        content_lower = content.lower()
        if any(word in content_lower for word in ['crítica', 'crítico', 'emergencia']):
            return UrgencyLevel.CRITICAL
        elif any(word in content_lower for word in ['alta', 'urgente', 'inmediato']):
            return UrgencyLevel.HIGH
        elif any(word in content_lower for word in ['media', 'moderada']):
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW
    
    def _extract_treatment_plan(self, content: str) -> List[str]:
        """Extrae plan de tratamiento"""
        lines = content.split('\n')
        treatment_section = False
        treatments = []
        
        for line in lines:
            if line.startswith('TRATAMIENTO:'):
                treatment_section = True
                treatment = line.replace('TRATAMIENTO:', '').strip()
                if treatment:
                    treatments.append(treatment)
            elif treatment_section and line.strip():
                if line.startswith('-') or line.startswith('*'):
                    treatments.append(line.strip()[1:].strip())
        
        return treatments[:5]  # Limitar a 5 tratamientos
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extrae recomendaciones"""
        lines = content.split('\n')
        recommendations_section = False
        recommendations = []
        
        for line in lines:
            if line.startswith('RECOMENDACIONES:'):
                recommendations_section = True
                continue
            elif recommendations_section and line.strip():
                if line.startswith('-') or line.startswith('*') or line[0].isdigit():
                    recommendations.append(line.strip())
        
        return recommendations[:8]  # Limitar a 8 recomendaciones
    
    def _calculate_confidence(
        self,
        sensor_data: SensorData,
        vision_results: Optional[Dict[str, Any]],
        rag_context: List[str],
        llm_response: Dict[str, Any]
    ) -> float:
        """Calcula confianza del diagnóstico"""
        base_confidence = 0.5
        
        # Aumentar confianza si hay datos de visión
        if vision_results:
            base_confidence += 0.2
            
            # Más confianza si la detección es alta
            vision_confidence = vision_results.get("confidence", 0)
            base_confidence += vision_confidence * 0.1
        
        # Aumentar confianza si hay contexto RAG
        if rag_context:
            base_confidence += 0.2
        
        # Ajustar según calidad de respuesta del LLM
        if llm_response.get("success", False):
            base_confidence += 0.1
        
        # Limitar entre 0.3 y 0.95
        return min(0.95, max(0.3, base_confidence))

class EmergencyDiagnosticUseCase(PlantDiagnosticUseCase):
    """Caso de uso especializado para emergencias"""
    
    async def emergency_diagnosis(
        self, 
        sensor_data: Dict[str, Any], 
        vision_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Diagnóstico de emergencia con acción inmediata"""
        try:
            # Identificar condiciones críticas
            critical_conditions = self._identify_critical_conditions(sensor_data, vision_results)
            
            if critical_conditions:
                # Generar prompt de emergencia
                emergency_prompt = MoleAIPrompts.get_emergency_assessment_prompt(
                    {"sensor_data": sensor_data, "vision_results": vision_results},
                    "\n".join(critical_conditions)
                )
                
                # Respuesta prioritaria
                llm_response = await self.llm_provider.generate_response(
                    prompt=emergency_prompt,
                    context=critical_conditions
                )
                
                # Procesar como diagnóstico de emergencia
                diagnosis = self._process_emergency_response(
                    llm_response, sensor_data, vision_results
                )
                
                # Guardar como emergencia
                diagnosis.urgency_level = UrgencyLevel.CRITICAL
                await self.persistence.save_diagnosis(diagnosis.to_dict())
                
                return diagnosis.to_dict()
            
            # Si no es emergencia, hacer diagnóstico normal
            return await self.diagnose_plant(sensor_data, vision_results)
            
        except Exception as e:
            raise DiagnosticError(f"Error en diagnóstico de emergencia: {str(e)}")
    
    def _identify_critical_conditions(
        self, 
        sensor_data: Dict[str, Any], 
        vision_results: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Identifica condiciones críticas"""
        critical = []
        
        # Condiciones críticas de sensores
        if float(sensor_data.get("soil_moisture", 100)) < 15:
            critical.append("Humedad del suelo críticamente baja - Riesgo de muerte inminente")
        
        if float(sensor_data.get("temperature", 25)) > 45:
            critical.append("Temperatura extrema - Daño celular grave")
        
        if float(sensor_data.get("ph", 7)) < 4 or float(sensor_data.get("ph", 7)) > 9:
            critical.append("pH extremo - Toxicidad del suelo")
        
        # Condiciones críticas de visión
        if vision_results:
            health_status = vision_results.get("health_status", "")
            if "multiple_issues" in health_status:
                critical.append("Múltiples problemas detectados - Riesgo de colapso")
        
        return critical
    
    def _process_emergency_response(
        self, 
        llm_response: Dict[str, Any],
        sensor_data: Dict[str, Any],
        vision_results: Optional[Dict[str, Any]]
    ) -> PlantDiagnosis:
        """Procesa respuesta de emergencia"""
        # Implementar procesamiento especializado para emergencias
        # ... (similar a _process_llm_response pero enfocado en emergencias)
        pass