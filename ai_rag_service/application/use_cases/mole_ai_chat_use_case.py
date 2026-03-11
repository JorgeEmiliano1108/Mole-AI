"""
Application Layer - Enhanced Chat Use Case with Mole-AI Agricultural Intelligence

AUDIT REFACTORING NOTES:
- Sensor validation now delegated to SensorValidator (Domain).
- Prompt construction now delegated to PromptBuilder (Domain).
- This Use Case is the ORCHESTRATOR: it connects validation, context building,
  prompt assembly, and LLM invocation - but owns none of the business rules.
"""
import logging
import time
from typing import List, Optional

from domain.models import (
    ChatRequest, ChatResponse
)
from domain.ports import LLMGenerationPort, VectorStorePort
from domain.services.mole_ai_agricultural_service import (
    MoleAIAgriculturalService,
    TacticalAlert,
    AgriculturalRecipe
)
from domain.services.prompt_builder import PromptBuilder
from domain.services.validator_service import (
    SensorValidator,
    InputSanitizer,
    ValidationError
)
from infrastructure.external.conabio_adapter import ConabioService


logger = logging.getLogger(__name__)


class MoleAIChatUseCase:
    """Enhanced chat use case with agricultural intelligence and tactical alerts"""

    def __init__(self, llm_service: LLMGenerationPort, vector_store: VectorStorePort = None):
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.mole_ai_service = MoleAIAgriculturalService()
        logger.info("Mole-AI Enhanced Chat Use Case initialized")

    async def execute(self, request: ChatRequest) -> ChatResponse:
        """Execute enhanced chat generation with agricultural intelligence"""
        start_time = time.time()

        try:
            # ================================================================
            # Step 0: INPUT VALIDATION & SANITIZATION (Audit Fix)
            # ================================================================
            from application.guardrails.input_guardrail import InputGuardrail
            
            guardrail = InputGuardrail()
            is_safe, sanitized_query = guardrail.validate(request.query)
            
            if not is_safe:
                logger.warning(f"🚫 Prompt injection blocked: {request.query[:100]}")
                return ChatResponse(
                    answer="⚠️ Tu solicitud ha sido bloqueada por seguridad. "
                           "No se permiten instrucciones que intenten modificar mi comportamiento.",
                    model_used="guardrail_blocked",
                    tokens_generated=0,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            sanitized_query = sanitized_query or request.query
            sanitized_context = InputSanitizer.sanitize_context(request.context or [])

            validated_sensor_data = None
            if request.sensor_data:
                try:
                    validated_sensor_data = SensorValidator.validate(request.sensor_data)
                except ValidationError as ve:
                    logger.error(f"Sensor validation failed: {ve}")
                    # Return immediately with error rather than hallucinating
                    return ChatResponse(
                        answer=f"⚠️ Error de validación de sensores: {ve}. "
                               f"Verifica los datos del dispositivo antes de continuar.",
                        model_used="validation_layer",
                        tokens_generated=0,
                        processing_time_ms=(time.time() - start_time) * 1000
                    )

            logger.info(f"Mole-AI processing query: {sanitized_query[:50]}...")

            # ================================================================
            # Step 1: RAG Retrieval
            # ================================================================
            rag_context: List[str] = []
            if self.vector_store:
                try:
                    chunks = await self.vector_store.retrieve(sanitized_query, top_k=3)
                    if chunks:
                        rag_context = [
                            f"FUENTE ({c.metadata.get('source', 'unknown')}): {c.content}"
                            for c in chunks
                        ]
                        logger.info(f"RAG retrieved {len(chunks)} chunks")
                except Exception as e:
                    logger.warning(f"RAG retrieval failed (degraded mode): {e}")

            # ================================================================
            # Step 2: Tactical Alerts from Sensor Data (Domain Service)
            # ================================================================
            tactical_alerts: List[TacticalAlert] = []
            if validated_sensor_data:
                tactical_alerts = self.mole_ai_service.analyze_sensor_data(validated_sensor_data)
                logger.info(f"Generated {len(tactical_alerts)} tactical alerts")

            # ================================================================
            # Step 3: Crop Detection
            # ================================================================
            crop_keywords = ["maíz", "maiz", "chile", "frijol", "calabaza", "tomate", "chili", "corn"]
            detected_crop = None
            for keyword in crop_keywords:
                if keyword.lower() in sanitized_query.lower():
                    detected_crop = keyword
                    break

            crop_context_str = None
            if detected_crop:
                crop_info = self.mole_ai_service.get_crop_info(detected_crop)
                if crop_info:
                    crop_context_str = (
                        f"{crop_info['common_name'].upper()} — "
                        f"pH óptimo: {crop_info['optimal_ph'][0]}-{crop_info['optimal_ph'][1]}, "
                        f"Humedad ideal: {crop_info['humidity_range'][0]}-{crop_info['humidity_range'][1]}%"
                    )

            # ================================================================
            # Step 3.5: CONABIO Species Lookup (External Service)
            # ================================================================
            if ConabioService.looks_like_species_query(sanitized_query):
                try:
                    species_data = await ConabioService.search_species(sanitized_query)
                    if species_data:
                        species_context = ConabioService.format_for_prompt(species_data)
                        rag_context.append(species_context)
                        logger.info(f"CONABIO species data injected: {species_data.get('nombre_cientifico', '?')}")
                except Exception as e:
                    logger.warning(f"CONABIO lookup failed (non-critical): {e}")

            # ================================================================
            # Step 4: Build Prompt (Domain Service - Single Source of Truth)
            # ================================================================
            prompt = PromptBuilder.build_chat_prompt(
                query=sanitized_query,
                context=sanitized_context,
                rag_context=rag_context,
                sensor_data=validated_sensor_data,
                tactical_alerts=tactical_alerts,
                crop_context=crop_context_str,
            )

            # ================================================================
            # Step 5: Treatment Recipe (if user asks for one)
            # ================================================================
            treatment_recipe: Optional[AgriculturalRecipe] = None
            treatment_keywords = ["tratamiento", "remedio", "receta", "cura", "solución"]
            if any(word in sanitized_query.lower() for word in treatment_keywords):
                treatment_recipe = self.mole_ai_service.recommend_organic_treatment(
                    condition=sanitized_query,
                    crop_type=detected_crop
                )

            # ================================================================
            # Step 6: LLM Generation (Adapter receives pre-built prompt)
            # ================================================================
            enhanced_request = ChatRequest(
                query=prompt,  # Full prompt goes as query
                context=[],    # Context is already embedded in prompt
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                sensor_data=None,  # Already in prompt
                image=request.image
            )

            llm_response = await self.llm_service.generate_response(enhanced_request)

            # ================================================================
            # Step 7: Post-processing (add structured recipe if applicable)
            # ================================================================
            final_answer = self._enhance_response_with_tactical_info(
                llm_response.answer,
                tactical_alerts,
                treatment_recipe,
                detected_crop
            )

            processing_time = (time.time() - start_time) * 1000

            response = ChatResponse(
                answer=final_answer,
                model_used=llm_response.model_used,
                tokens_generated=llm_response.tokens_generated,
                processing_time_ms=processing_time
            )

            logger.info(f"Mole-AI response generated in {processing_time:.2f}ms")
            return response

        except Exception as e:
            logger.error(f"Error in MoleAIChatUseCase: {str(e)}")
            raise

    def _enhance_response_with_tactical_info(
        self,
        original_answer: str,
        tactical_alerts: list,
        treatment_recipe: Optional[AgriculturalRecipe] = None,
        detected_crop: str = None
    ) -> str:
        """Enhance LLM response with tactical agricultural information"""

        enhanced = original_answer

        # Add structured recipe if available and not already in response
        if treatment_recipe and "## RECETA" not in original_answer.upper():
            recipe_section = f"""

---
## 🧪 RECETA DETALLADA - {treatment_recipe.name.upper()}

### 📦 Ingredientes:
"""
            for ingredient in treatment_recipe.ingredients:
                for name, quantity in ingredient.items():
                    recipe_section += f"- **{name}**: {quantity}\n"

            recipe_section += f"""
### 🔬 Preparación:
{treatment_recipe.preparation}

### 🌿 Aplicación:
{treatment_recipe.application_method}

### ⏰ Frecuencia:
{treatment_recipe.frequency}

### ⚠️ Notas de Seguridad:
"""
            for note in treatment_recipe.safety_notes:
                recipe_section += f"- {note}\n"

            enhanced += recipe_section

        # Add crop-specific recommendations
        if detected_crop and "RECOMENDACIONES ESPECÍFICAS" not in original_answer.upper():
            crop_info = self.mole_ai_service.get_crop_info(detected_crop)
            if crop_info:
                enhanced += f"""

---
## 🌱 RECOMENDACIONES ESPECÍFICAS - {crop_info['common_name'].upper()}

**Necesidades Nutricionales:**
- Nitrógeno (N): {crop_info['nutrients_needs']['N']}
- Fósforo (P): {crop_info['nutrients_needs']['P']}
- Potasio (K): {crop_info['nutrients_needs']['K']}

**Parámetros Óptimos:**
- pH del suelo: {crop_info['optimal_ph'][0]} - {crop_info['optimal_ph'][1]}
- Humedad ambiental: {crop_info['humidity_range'][0]}% - {crop_info['humidity_range'][1]}%
- Temperatura: {crop_info['temperature_range'][0]}°C - {crop_info['temperature_range'][1]}°C
"""

        return enhanced