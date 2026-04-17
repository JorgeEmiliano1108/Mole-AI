from ms2_rag_cag_service.domain.models import ChatRequest, ChatResponse
from ms2_rag_cag_service.infrastructure.redis_sensor_cache_adapter import RedisSensorCacheAdapter
from ms2_rag_cag_service.infrastructure.citation_manager import CitationManager
from ms2_rag_cag_service.infrastructure.faiss_vector_store import FAISSVectorStore
from ms2_rag_cag_service.infrastructure.prompt_loader import load_prompt
from ms2_rag_cag_service.infrastructure.llm_client import LLMClient
import logging
import os
import aiohttp 
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger("ms2.chat_usecase")

class MoleAIChatUseCase:
    def __init__(self):
        self.redis_adapter = RedisSensorCacheAdapter(os.getenv("REDIS_URL", "redis://redis:6379/0"))
        self.vector_store = FAISSVectorStore()
        self.citation_manager = CitationManager()
        self.trefle_token = os.getenv("TREFLE_API_TOKEN", "")
        
        model_name = os.getenv("LLM_MODEL_ID", "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B")
        self.llm_client = LLMClient(model_name=model_name)
        
        try:
            self.system_prompt = load_prompt("agronomist")
        except Exception:
            logger.warning("[MoleAIChatUseCase] Could not load agronomist prompt; using strict default.")
            self.system_prompt = (
                "Eres Mole.AI, un asistente agrónomo experto especializado en flora. "
                "REGLA DE ORO: Si la información proporcionada en el CONTEXTO DISPONIBLE "
                "(sensores, base local o Trefle API) no contiene la respuesta, DEBES "
                "responder textualmente: 'No tengo suficiente información científica "
                "para responder esto con seguridad.' "
                "NUNCA inventes nombres científicos, tratamientos ni propiedades."
            )

    async def _search_trefle_api(self, query: str) -> str:
        """Motor de respaldo que consulta la API de botánica si FAISS falla."""
        if not self.trefle_token:
            return ""
            
        logger.info(f"FAISS insuficiente. Consultando Trefle.io API para: '{query}'")
        url = f"https://trefle.io/api/v1/plants/search?token={self.trefle_token}&q={query}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data"):
                            # Extraemos la primera planta encontrada como contexto
                            plant = data["data"][0]
                            return f"Datos de Trefle.io -> Nombre Científico: {plant.get('scientific_name')}, Familia: {plant.get('family_common_name', 'Desconocida')}, Nombre Común: {plant.get('common_name', 'Desconocido')}."
        except Exception as e:
            logger.error(f"Error consultando Trefle.io: {e}")
        return ""

    async def ainvoke(self, request: ChatRequest) -> ChatResponse:
        logger.info(f"Procesando consulta para User {request.user_id}: {request.message[:50]}...")
        
        # 1. Recuperación de Contexto Base
        cag_context = await self.redis_adapter.get_context(request.user_id)
        rag_context, rag_sources = await self.vector_store.asearch(request.message)
        
        has_sufficient_context = bool(rag_context and len(rag_context.strip()) > 10)
        trefle_context = ""

        # 2. Plan B: Si RAG local falló, consultamos a internet (Trefle.io)
        if not has_sufficient_context:
            trefle_context = await self._search_trefle_api(request.message)
            if trefle_context:
                has_sufficient_context = True

        # 3. Empaquetado de Datos para el LLM
        full_context = {
            "telemetria_sensores": cag_context if cag_context else "No hay datos de sensores en vivo.",
            "base_conocimiento_local": rag_context if rag_context else "No hay documentos locales relevantes.",
            "base_conocimiento_externa": trefle_context if trefle_context else "No se encontraron datos en internet."
        }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt + "\n\nCONTEXTO DISPONIBLE:\n{context}"),
            ("user", request.message)
        ])
        
        try:
            # 4. Inferencia con prevención de alucinaciones
            raw_validated: ChatResponse = await self.llm_client.generate(prompt.format_prompt(context=full_context).to_string())
            
            # 5. Gestión de Fuentes
            if not has_sufficient_context:
                raw_validated.sources = []
            elif not getattr(raw_validated, "sources", []):
                # Pasamos el dict completo para que CitationManager extraiga las fuentes
                raw_validated.sources = await self.citation_manager.extract_sources(full_context) or []

            return raw_validated

        except Exception as e:
            logger.error(f"[MoleAIChatUseCase] Fallo crítico en la generación LLM: {e}", exc_info=True)
            # CORRECCIÓN: Instanciación ESTRICTA Pydantic v2 (usando "respuesta")
            return ChatResponse(
                respuesta="Ocurrió un error de conexión con el modelo de Inteligencia Artificial. Por favor, intenta de nuevo.",
                sources=[],
                disclaimer="AVISO LEGAL: Sistema en contingencia. La información es estrictamente informativa."
            )