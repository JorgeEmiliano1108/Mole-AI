"""Chat Use Case

Orquesta la lógica de RAG + CAG + LLM con sanitización PII y REGLA DE ORO.
Se utiliza en la API y en los tests.
"""

import structlog

from app.core.pii_sanitizer import PIISanitizer
from app.domain.protocols import LLMClientPort, VectorStorePort, RedisAdapterPort, CitationManagerPort
from app.domain.schemas import ChatRequest, ChatResponse

logger = structlog.get_logger()

REGLA_DE_ORO = (
    "REGLA DE ORO: Si la información proporcionada en el CONTEXTO DISPONIBLE "
    "(sensores, base local o Trefle API) no contiene la respuesta, DEBES "
    "responder textualmente: 'No tengo suficiente información científica "
    "para responder esto con seguridad.' "
    "NUNCA inventes nombres científicos, tratamientos ni propiedades."
)


class MoleAIChatUseCase:
    """Caso de uso principal para el chat.

    - Sanitiza PII (email/teléfono) del mensaje antes de procesarlo.
    - Hashea user_id en logs (LFPDPPP).
    - Inyecta REGLA DE ORO anti‑alucinación en el system prompt.
    - Obtiene contexto del sensor vía Redis.
    - Busca información relevante en el vector store.
    - Llama al LLM client para generar la respuesta.
    - Permite inyección de dependencias para pruebas.
    """

    def __init__(self, *, redis_adapter: RedisAdapterPort,
                 vector_store: VectorStorePort,
                 llm_client: LLMClientPort,
                 citation_manager: CitationManagerPort | None = None,
                 system_prompt: str | None = None):
        self.redis_adapter = redis_adapter
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.citation_manager = citation_manager
        self._custom_prompt = system_prompt

    async def _search_trefle_api(self, plant_name: str) -> str:
        """Placeholder para buscar información en la API Trefle.
        En producción se implementaría la lógica real.
        Los tests lo mockean.
        """
        return ""

    async def ainvoke(self, request: ChatRequest) -> ChatResponse:
        """Orquesta la cadena completa y devuelve un ``ChatResponse``.

        Pasos:
        1. Hashear user_id y sanitizar mensaje (PII).
        2. Obtener contexto del sensor.
        3. Buscar en el vector store.
        4. Montar prompt con REGLA DE ORO + contexto multi-fuente.
        5. Generar respuesta con LLM.
        """
        # ── PII Sanitization (LFPDPPP) ──────────────────────────────
        hashed_id = PIISanitizer.hash_user_id(request.user_id)
        logger.info("procesando_consulta", user_hash=hashed_id)
        mensaje_seguro = PIISanitizer.sanitize(request.message)

        # 1. Contexto del sensor (puede ser dict o string)
        sensor_context = await self.redis_adapter.get_context(request.user_id)
        if isinstance(sensor_context, dict):
            sensor_context = sensor_context.get("context") or ""

        # 2. Búsqueda vectorial (con mensaje sanitizado)
        vector_context, sources = await self.vector_store.asearch(mensaje_seguro)

        # 3. Montar prompt – siempre anteponer REGLA DE ORO
        system_prompt = self._custom_prompt or (
            "Eres Mole.AI, un asistente agrónomo experto especializado en flora.\n"
        )
        system_prompt = f"{REGLA_DE_ORO}\n\n{system_prompt}"
        if sensor_context:
            system_prompt += f"Contexto del sensor: {sensor_context}\n"
        if vector_context:
            system_prompt += f"Contexto de la base: {vector_context}\n"

        # 4. Llamada al LLM (con mensaje sanitizado)
        llm_response = await self.llm_client.generate(system_prompt, mensaje_seguro)

        # Incorporar fuentes obtenidas de la búsqueda vectorial si el LLM no las incluye
        if not llm_response.sources:
            llm_response.sources = sources
        return llm_response
