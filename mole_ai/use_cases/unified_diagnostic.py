import logging
import time
from typing import Optional
from datetime import datetime

from ..domain.ports import (
    VisionProviderPort,
    KnowledgeRetrievalPort,
    SensorDataPort,
    DiagnosticPersistencePort,
    ModelManagementPort,
    NotificationPort
)
from ..domain.models.plant import (
    PlantDiagnosis, 
    PlantImage, 
    SensorData, 
    KnowledgeContext,
    PlantState
)
from ..domain.exceptions import (
    VisionAnalysisError,
    KnowledgeRetrievalError,
    SensorDataError,
    PersistenceError,
    ModelNotReadyError,
    ConfidenceThresholdError
)

logger = logging.getLogger(__name__)


class UnifiedDiagnosticUseCase:
    """Caso de uso unificado para diagnóstico completo de plantas"""
    
    def __init__(
        self,
        vision_provider: VisionProviderPort,
        knowledge_retriever: KnowledgeRetrievalPort,
        sensor_data: SensorDataPort,
        persistence: DiagnosticPersistencePort,
        model_manager: ModelManagementPort,
        notification_service: Optional[NotificationPort] = None
    ):
        self.vision_provider = vision_provider
        self.knowledge_retriever = knowledge_retriever
        self.sensor_data = sensor_data
        self.persistence = persistence
        self.model_manager = model_manager
        self.notification_service = notification_service

    async def execute_complete_diagnosis(
        self,
        image: PlantImage,
        sensor_input: Optional[SensorData] = None,
        plant_id: Optional[str] = None,
        force_rag_query: Optional[str] = None
    ) -> PlantDiagnosis:
        """
        Ejecuta diagnóstico completo unificado:
        1. Análisis visual con Phi-3.5
        2. Recuperación de conocimiento RAG
        3. Integración con datos de sensores
        4. Generación de diagnóstico final
        5. Persistencia y notificaciones
        """
        start_time = time.time()
        
        try:
            logger.info(f"Iniciando diagnóstico unificado para planta {plant_id or 'desconocida'}")
            
            # 1. Validar que el modelo esté listo
            if not await self.model_manager.is_model_ready():
                raise ModelNotReadyError("Modelo Phi-3.5 no está listo para inferencia")
            
            # 2. Obtener datos de sensores (usar input o último disponible)
            sensores = sensor_input or await self.sensor_data.get_latest_sensor_data(plant_id)
            
            # 3. Análisis visual con Phi-3.5
            logger.info("Ejecutando análisis visual con Phi-3.5...")
            vision_result = await self.vision_provider.analyze_plant_image(
                image=image,
                context=self._create_vision_context(sensores)
            )
            
            # 4. Recuperación de conocimiento RAG
            logger.info("Recuperando conocimiento agronómico...")
            query = force_rag_query or self._create_rag_query(vision_result, sensores)
            knowledge_results = await self.knowledge_retriever.get_relevant_knowledge(
                query=query,
                top_k=3
            )
            
            # 5. Integración y generación de diagnóstico final
            logger.info("Generando diagnóstico integrado...")
            diagnosis = await self._generate_integrated_diagnosis(
                image=image,
                sensores=sensores,
                vision_result=vision_result,
                knowledge_results=knowledge_results,
                plant_id=plant_id,
                inference_time=time.time() - start_time
            )
            
            # 6. Persistencia
            await self.persistence.save_diagnosis(diagnosis)
            
            # 7. Notificaciones si es necesario
            if self.notification_service and diagnosis.requiere_accion_humana:
                await self._send_notifications(diagnosis)
            
            logger.info(f"✅ Diagnóstico completado: {diagnosis.estado} (confianza: {diagnosis.confianza:.2f})")
            return diagnosis
            
        except Exception as e:
            logger.error(f"Error en diagnóstico unificado: {str(e)}")
            raise

    async def execute_vision_only_diagnosis(
        self,
        image: PlantImage,
        context: Optional[str] = None
    ) -> dict:
        """Ejecuta solo análisis visual (modo rápido)"""
        try:
            if not await self.model_manager.is_model_ready():
                raise ModelNotReadyError("Modelo no listo")
            
            return await self.vision_provider.analyze_plant_image(image, context)
            
        except Exception as e:
            logger.error(f"Error en diagnóstico visual: {str(e)}")
            raise VisionAnalysisError(f"Error análisis visual: {str(e)}")

    async def execute_knowledge_retrieval(
        self,
        query: str,
        filters: Optional[dict] = None,
        top_k: int = 3
    ) -> list:
        """Ejecuta solo recuperación de conocimiento"""
        try:
            return await self.knowledge_retriever.get_relevant_knowledge(
                query=query,
                filters=filters,
                top_k=top_k
            )
        except Exception as e:
            logger.error(f"Error recuperación conocimiento: {str(e)}")
            raise KnowledgeRetrievalError(f"Error RAG: {str(e)}")

    def _create_vision_context(self, sensores: SensorData) -> str:
        """Crea contexto para análisis visual basado en sensores"""
        context_parts = []
        
        if sensores.ph < 5.5:
            context_parts.append("Suelo ácido detectado - posible deficiencia nutricional")
        elif sensores.ph > 7.5:
            context_parts.append("Suelo alcalino - posible bloqueo de nutrientes")
        
        if sensores.humedad > 80:
            context_parts.append("Alta humedad ambiental - riesgo de enfermedades fúngicas")
        elif sensores.humedad < 40:
            context_parts.append("Baja humedad - posible estrés hídrico")
        
        if sensores.temp > 30:
            context_parts.append("Temperatura elevada - estrés térmico posible")
        elif sensores.temp < 15:
            context_parts.append("Temperatura baja - metabolismo reducido")
        
        if sensores.uv > 1.0:
            context_parts.append("Alta radiación UV - posible fotoestrés")
        
        return "; ".join(context_parts) if context_parts else "Condiciones ambientales normales"

    def _create_rag_query(
        self,
        vision_result: dict,
        sensores: SensorData
    ) -> str:
        """Crea query para RAG basado en análisis visual y sensores"""
        query_parts = []
        
        # Síntomas visuales
        if vision_result.get('sintomas_visibles'):
            query_parts.append(f"síntomas: {', '.join(vision_result['sintomas_visibles'])}")
        
        # Estado detectado
        if vision_result.get('estado'):
            query_parts.append(f"estado: {vision_result['estado']}")
        
        # Condiciones ambientales
        env_conditions = []
        if sensores.ph < 5.5 or sensores.ph > 7.5:
            env_conditions.append(f"pH {sensores.ph:.1f}")
        if sensores.humedad > 80:
            env_conditions.append(f"humedad alta {sensores.humedad:.0f}%")
        if sensores.temp > 30:
            env_conditions.append(f"temperatura alta {sensores.temp:.1f}°C")
        
        if env_conditions:
            query_parts.append(f"condiciones: {', '.join(env_conditions)}")
        
        # Especie si está identificada
        if vision_result.get('especie_probable') and vision_result['especie_probable'] != 'Desconocida':
            query_parts.append(f"especie: {vision_result['especie_probable']}")
        
        return "diagnóstico tratamiento " + " ".join(query_parts)

    async def _generate_integrated_diagnosis(
        self,
        image: PlantImage,
        sensores: SensorData,
        vision_result: dict,
        knowledge_results: list,
        plant_id: Optional[str],
        inference_time: float
    ) -> PlantDiagnosis:
        """Genera diagnóstico integrado combinando visión, RAG y sensores"""
        
        # Extraer conocimiento relevante
        knowledge_context = self._extract_knowledge_context(knowledge_results)
        
        # Determinar estado final basado en múltiples factores
        estado_final = self._determine_final_state(vision_result, sensores)
        
        # Calcular confianza integrada
        confianza_final = self._calculate_integrated_confidence(
            vision_result.get('confianza', 0.5),
            knowledge_results,
            sensores
        )
        
        # Generar diagnóstico técnico
        diagnostico_tecnico = self._generate_technical_diagnosis(
            vision_result,
            sensores,
            knowledge_context
        )
        
        # Generar recomendaciones
        recomendaciones = self._generate_recommendations(
            estado_final,
            vision_result,
            sensores,
            knowledge_context
        )
        
        # Compilar síntomas
        sintomas = self._compile_symptoms(vision_result, sensores)
        
        # Fuentes
        fuentes = [k.get('fuentes', ['General'])[0] for k in knowledge_results]
        
        # Crear diagnóstico
        diagnosis = PlantDiagnosis(
            plant_id=plant_id,
            imagen=image,
            sensores=sensores,
            conocimiento=KnowledgeContext(
                documentos=sum([k.get('documentos', []) for k in knowledge_results], []),
                fuentes=fuentes,
                scores_relevancia=sum([k.get('scores_relevancia', []) for k in knowledge_results], []),
                tema_principal=knowledge_results[0].get('tema_principal', 'general') if knowledge_results else None
            ),
            estado=estado_final,
            confianza=confianza_final,
            especie=vision_result.get('especie_probable'),
            sintomas=sintomas,
            diagnostico=diagnostico_tecnico,
            recomendaciones=recomendaciones,
            fuentes=list(set(fuentes)),
            modelo_utilizado="Phi-3.5 Vision-Instruct Q4",
            tiempo_inferencia=inference_time,
            requiere_accion_humana=confianza_final < 0.85 or estado_final == PlantState.PELIGRO
        )
        
        return diagnosis

    def _extract_knowledge_context(self, knowledge_results: list) -> str:
        """Extrae contexto relevante del conocimiento recuperado"""
        if not knowledge_results:
            return "Contexto no disponible"
        
        context_parts = []
        for result in knowledge_results[:2]:  # Los 2 más relevantes
            documentos = result.get('documentos', [])
            if documentos:
                context_parts.append(documentos[0] if isinstance(documentos, list) else documentos)
        
        return " | ".join(context_parts)

    def _determine_final_state(self, vision_result: dict, sensores: SensorData) -> PlantState:
        """Determina estado final basado en análisis integrado"""
        vision_state = vision_result.get('estado', 'Atención')
        vision_confidence = vision_result.get('confianza', 0.5)
        
        # Factores de riesgo ambientales
        risk_factors = 0
        
        if sensores.ph < 5.0 or sensores.ph > 8.0:
            risk_factors += 2
        elif sensores.ph < 5.5 or sensores.ph > 7.5:
            risk_factors += 1
            
        if sensores.humedad > 85:
            risk_factors += 2
        elif sensores.humedad > 80:
            risk_factors += 1
            
        if sensores.temp > 35 or sensores.temp < 10:
            risk_factors += 2
        elif sensores.temp > 30 or sensores.temp < 15:
            risk_factors += 1
        
        # Ajustar estado basado en factores de riesgo
        if vision_state == "Peligro":
            return PlantState.PELIGRO
        elif vision_state == "Sana" and risk_factors == 0:
            return PlantState.SANA
        elif risk_factors >= 3:
            return PlantState.PELIGRO
        elif risk_factors >= 1 or vision_state == "Atención":
            return PlantState.ATENCION
        else:
            return PlantState.SANA

    def _calculate_integrated_confidence(
        self,
        vision_confidence: float,
        knowledge_results: list,
        sensores: SensorData
    ) -> float:
        """Calcula confianza integrada ponderada"""
        
        # Confianza base del análisis visual
        base_confidence = vision_confidence
        
        # Ajuste por calidad del conocimiento recuperado
        knowledge_bonus = 0.0
        if knowledge_results:
            avg_relevance = sum([k.get('scores_relevancia', [0.5])[0] for k in knowledge_results]) / len(knowledge_results)
            knowledge_bonus = avg_relevance * 0.1  # Hasta 10% de bonus
        
        # Ajuste por consistencia de sensores
        sensor_consistency = 1.0
        if sensores.ph < 4.0 or sensores.ph > 9.0:
            sensor_consistency -= 0.2
        if sensores.humedad > 95 or sensores.humedad < 5:
            sensor_consistency -= 0.2
        if sensores.temp < -20 or sensores.temp > 50:
            sensor_consistency -= 0.2
        
        # Calcular confianza final
        integrated_confidence = base_confidence + knowledge_bonus
        integrated_confidence *= sensor_consistency
        
        # Limitar rango
        return max(0.0, min(1.0, integrated_confidence))

    def _generate_technical_diagnosis(
        self,
        vision_result: dict,
        sensores: SensorData,
        knowledge_context: str
    ) -> str:
        """Genera diagnóstico técnico integrado"""
        
        diagnosis_parts = []
        
        # Análisis visual
        if vision_result.get('análisis_visual'):
            diagnosis_parts.append(f"Análisis visual: {vision_result['análisis_visual']}")
        
        # Condiciones ambientales
        env_analysis = []
        if sensores.ph < 5.5:
            env_analysis.append(f"pH ácido ({sensores.ph:.1f}) con posible bloqueo de nutrientes")
        elif sensores.ph > 7.5:
            env_analysis.append(f"pH alcalino ({sensores.ph:.1f}) con riesgo de deficiencias")
        
        if sensores.humedad > 80:
            env_analysis.append(f"alta humedad ({sensores.humedad:.0f}%) favoreciendo enfermedades fúngicas")
        
        if env_analysis:
            diagnosis_parts.append(f"Condiciones ambientales: {', '.join(env_analysis)}")
        
        # Conocimiento especializado
        if knowledge_context and knowledge_context != "Contexto no disponible":
            diagnosis_parts.append(f"Evidencia agronómica: {knowledge_context[:200]}...")
        
        return " | ".join(diagnosis_parts) if diagnosis_parts else "Diagnóstico en proceso de análisis"

    def _generate_recommendations(
        self,
        estado: PlantState,
        vision_result: dict,
        sensores: SensorData,
        knowledge_context: str
    ) -> list:
        """Genera recomendaciones específicas"""
        
        recommendations = []
        
        # Recomendaciones por estado
        if estado == PlantState.PELIGRO:
            recommendations.append("Acción inmediata requerida - consultar especialista agrícola")
            recommendations.append("Monitorear diariamente hasta estabilización")
        
        # Recomendaciones por pH
        if sensores.ph < 5.5:
            recommendations.append("Aplicar cal agrícola para corregir acidez (consultar dosis)")
        elif sensores.ph > 7.5:
            recommendations.append("Aplicar azufre elemental o ácidos orgánicos para bajar pH")
        
        # Recomendaciones por humedad
        if sensores.humedad > 80:
            recommendations.append("Mejorar ventilación y reducir frecuencia de riego")
            recommendations.append("Considerar aplicación fungicida preventivo")
        
        # Recomendaciones por temperatura
        if sensores.temp > 30:
            recommendations.append("Proporcionar sombra durante horas pico de calor")
        elif sensores.temp < 15:
            recommendations.append("Proteger del frío, considerar cubierta térmica")
        
        # Recomendaciones por síntomas específicos
        sintomas = vision_result.get('sintomas_visibles', [])
        if 'manchas blancas' in str(sintomas).lower():
            recommendations.append("Investigar posible mildiú - aplicar fungicida específico")
        if 'amarillamiento' in str(sintomas).lower():
            recommendations.append("Evaluar deficiencias nutricionales - considerar análisis foliar")
        
        # Recomendación general si no hay suficientes
        if len(recommendations) < 2:
            recommendations.append("Continuar monitoreo regular y mantener condiciones óptimas")
        
        return recommendations[:5]  # Limitar a 5 recomendaciones

    def _compile_symptoms(self, vision_result: dict, sensores: SensorData) -> list:
        """Compila lista completa de síntomas"""
        symptoms = []
        
        # Síntomas visuales
        visual_symptoms = vision_result.get('sintomas_visibles', [])
        if isinstance(visual_symptoms, list):
            symptoms.extend(visual_symptoms)
        elif visual_symptoms:
            symptoms.append(visual_symptoms)
        
        # Síntomas por sensores
        if sensores.ph < 5.5:
            symptoms.append("síntomas de deficiencia nutricional por pH ácido")
        elif sensores.ph > 7.5:
            symptoms.append("síntomas de bloqueo de nutrientes por pH alcalino")
        
        if sensores.humedad > 85:
            symptoms.append("estrés por alta humedad ambiental")
        elif sensores.humedad < 30:
            symptoms.append("síntomas de estrés hídrico")
        
        return list(set(symptoms))  # Eliminar duplicados

    async def _send_notifications(self, diagnosis: PlantDiagnosis):
        """Envía notificaciones sobre diagnóstico crítico"""
        try:
            # Aquí se implementaría la lógica de notificación
            # Por ahora solo logging
            logger.warning(f"🚨 ALERTA: Diagnóstico crítico para planta {diagnosis.plant_id}")
            logger.warning(f"   Estado: {diagnosis.estado}")
            logger.warning(f"   Confianza: {diagnosis.confianza:.2f}")
            logger.warning(f"   Diagnóstico: {diagnosis.diagnostico[:100]}...")
            
        except Exception as e:
            logger.error(f"Error enviando notificaciones: {str(e)}")