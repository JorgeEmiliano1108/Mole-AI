from ms2_rag_cag_service.domain.models import ChatRequest, ChatResponse, SourceMetadata
from ms2_rag_cag_service.infrastructure.redis_sensor_cache_adapter import RedisSensorCacheAdapter
from ms2_rag_cag_service.infrastructure.citation_manager import CitationManager
from ms2_rag_cag_service.infrastructure.faiss_vector_store import FAISSVectorStore
from ms2_rag_cag_service.infrastructure.prompt_loader import load_prompt
from ms2_rag_cag_service.infrastructure.llm_client import LLMClient
import logging
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import ValidationError

class MoleAIChatUseCase:
    def __init__(self):
        self.redis_adapter = RedisSensorCacheAdapter(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        self.vector_store = FAISSVectorStore()
        self.citation_manager = CitationManager()
        model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        # use resilient LLM client with retries/fallback
        self.llm_client = LLMClient(model_name=model_name)
        # load system prompt from prompts directory
        try:
            self.system_prompt = load_prompt("agronomist")
        except Exception:
            logging.warning("[MoleAIChatUseCase] Could not load agronomist prompt; using safe default.")
            self.system_prompt = "Eres un asistente agrónomo. Responde con información verificada. Incluye sources y disclaimer si aplica."

    async def ainvoke(self, request: ChatRequest) -> ChatResponse:
        # 1. Obtener contexto CAG (Redis)
        cag_context = await self.redis_adapter.get_context(request.user_id)
        # 2. Obtener contexto RAG (FAISS)
        rag_context, rag_sources = await self.vector_store.asearch(request.message)
        # 3. Fusionar contextos
        full_context = {"cag": cag_context, "rag": rag_context}
        # 4. Extraer fuentes reales
        sources = await self.citation_manager.extract_sources(full_context)
        # 5. Construir prompt estructurado
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt + " Usa el siguiente contexto: {context}"),
            ("user", request.message)
        ])
        # 6. Llamar LLM de forma asíncrona y estructurada
        try:
            raw_validated = await self.llm_client.generate(prompt.format_prompt(context=full_context).to_string())
            # ensure sources are populated from citation manager if LLM omitted them
            if not getattr(raw_validated, "sources", None):
                raw_validated.sources = sources or []
            # ensure disclaimer present (default safe message if missing)
            if raw_validated.disclaimer in (None, ""):
                raw_validated.disclaimer = "COFEPRIS: Esta respuesta es informativa y no sustituye la consulta profesional."
            return raw_validated
        except Exception as e:
            logging.error(f"[MoleAIChatUseCase] LLM error: {e}")
            # On LLM call failures return a safe, structured ChatResponse without raising
            return ChatResponse.model_validate({
                "respuesta": "Ocurrió un error procesando tu solicitud.",
                "sources": sources or [],
                "disclaimer": "Esta respuesta es informativa y no sustituye la consulta profesional."
            })
