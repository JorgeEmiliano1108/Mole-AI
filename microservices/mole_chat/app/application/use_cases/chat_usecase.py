from app.domain.schemas import ChatRequest, ChatResponse
from app.infrastructure.adapters.redis_sensor_cache_adapter import RedisSensorCacheAdapter
from app.infrastructure.adapters.citation_manager import CitationManager
from app.infrastructure.adapters.pgvector_store import PgVectorStore
from app.infrastructure.adapters.prompt_loader import load_prompt
from app.infrastructure.adapters.llm_client import LLMClient
from app.core.pii_sanitizer import PIISanitizer 

import logging
import os
import aiohttp 
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger("ms2.chat_usecase")

class MoleAIChatUseCase:
    def __init__(
        self, 
        llm_client: LLMClient,
        vector_store: PgVectorStore,
        redis_adapter: RedisSensorCacheAdapter,
        citation_manager: CitationManager,
        system_prompt: str
    ):
        self.llm_client = llm_client
        self.vector_store = vector_store
        self.redis_adapter = redis_adapter
        self.citation_manager = citation_manager
        self.trefle_token = os.getenv("TREFLE_API_TOKEN", "")
        self.system_prompt = system_prompt
        
        if not system_prompt:
            logger.warning("[MoleAIChatUseCase] Using strict default prompt.")
            self.system_prompt = (
                "Eres Mole.AI, un asistente agrónomo experto especializado en flora. "
                "Si el usuario te saluda, te pregunta por tus capacidades o tiene una conversación general, "
                "explícalas de forma natural y amigable. "
                "REGLA DE ORO: Si el usuario hace una pregunta técnica o científica y la información "
                "proporcionada en el CONTEXTO DISPONIBLE no contiene la respuesta, DEBES "
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
                            plant = data["data"][0]
                            return f"Datos de Trefle.io -> Nombre Científico: {plant.get('scientific_name')}, Familia: {plant.get('family_common_name', 'Desconocida')}, Nombre Común: {plant.get('common_name', 'Desconocido')}."
        except Exception as e:
            logger.error(f"Error consultando Trefle.io: {e}")
        return ""

    async def ainvoke(self, request: ChatRequest) -> ChatResponse:
    
        hashed_id = PIISanitizer.hash_user_id(request.user_id)
        logger.info(f"Procesando consulta RAG+CAG", extra={"user_hash": hashed_id})
        
        mensaje_seguro = PIISanitizer.sanitize(request.message)
        
        # 1. Recuperación de Contexto Base
        cag_context = await self.redis_adapter.get_context(request.user_id)
        
        rag_context, rag_sources = await self.vector_store.asearch(mensaje_seguro)
        
        has_sufficient_context = bool(rag_context and len(rag_context.strip()) > 10)
        trefle_context = ""

        # 2. Plan B: Si RAG local falló, consultamos a internet (Trefle.io)
        if not has_sufficient_context:
            trefle_context = await self._search_trefle_api(mensaje_seguro)
            if trefle_context:
                has_sufficient_context = True

        # 3. Empaquetado de Datos para el LLM
        full_context = {
            "telemetria_sensores": cag_context if cag_context else "No hay datos de sensores en vivo.",
            "base_conocimiento_local": rag_context if rag_context else "No hay documentos locales relevantes.",
            "base_conocimiento_externa": trefle_context if trefle_context else "No se encontraron datos en internet."
        }
        
        # 🛡️ Inyectamos el 'mensaje_seguro' en lugar del crudo
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt + "\n\nCONTEXTO DISPONIBLE:\n{context}"),
            ("user", mensaje_seguro) 
        ])
        
        try:
            # 4. Inferencia con prevención de alucinaciones
            raw_validated: ChatResponse = await self.llm_client.generate(prompt.format_prompt(context=full_context).to_string())
            
            # 5. Gestión de Fuentes
            if not has_sufficient_context:
                raw_validated.sources = []
            elif not getattr(raw_validated, "sources", []):
                raw_validated.sources = await self.citation_manager.extract_sources(full_context) or []

            return raw_validated

        except Exception as e:
            logger.error(f"[MoleAIChatUseCase] Fallo crítico en la generación LLM", exc_info=True, extra={"user_hash": hashed_id})
            return ChatResponse(
                respuesta="Ocurrió un error de conexión con el modelo de Inteligencia Artificial. Por favor, intenta de nuevo.",
                sources=[],
                disclaimer="AVISO LEGAL: Sistema en contingencia. La información es estrictamente informativa."
            )