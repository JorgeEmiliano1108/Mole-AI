from app.domain.schemas import ChatRequest, ChatResponse
from app.infrastructure.adapters.redis_sensor_cache_adapter import RedisSensorCacheAdapter
from app.infrastructure.adapters.citation_manager import CitationManager
from app.infrastructure.adapters.pgvector_store import PgVectorStore
from app.infrastructure.adapters.prompt_loader import load_prompt
from app.infrastructure.adapters.llm_client import LLMClient
from app.core.pii_sanitizer import PIISanitizer

import json
import logging
import os
import aiohttp

logger = logging.getLogger("ms2.chat_usecase")


_BASE_SYSTEM_PROMPT = (
    "Eres Mole.AI, un asistente agrónomo experto especializado en flora. "
    "Si el usuario te saluda o pregunta por tus capacidades, explícalas de forma natural. "
    "REGLA DE ORO: Si la información en el CONTEXTO DISPONIBLE no contiene la respuesta, "
    "responde textualmente: 'No tengo suficiente información científica para responder esto con seguridad.' "
    "NUNCA inventes nombres científicos, tratamientos ni propiedades."
)


def _build_system_prompt(base: str, sensor_data: dict | str, rag_context: str, trefle_context: str) -> str:
    """Construye el system prompt final inyectando telemetría IoT y contexto RAG."""
    # Normalizar sensor_data (puede llegar como str JSON o dict)
    if isinstance(sensor_data, str):
        try:
            sensor_data = json.loads(sensor_data)
        except Exception:
            sensor_data = {}

    humidity = sensor_data.get("humidity", sensor_data.get("humedad", "N/D"))
    temperature = sensor_data.get("temperature", sensor_data.get("temperatura", "N/D"))
    ph = sensor_data.get("ph", "N/D")
    ec = sensor_data.get("ec", sensor_data.get("conductividad", "N/D"))

    iot_block = (
        f"TELEMETRÍA EN VIVO (ESP32):\n"
        f"  - Temperatura: {temperature}°C\n"
        f"  - Humedad: {humidity}%\n"
        f"  - pH estimado suelo: {ph}\n"
        f"  - Conductividad eléctrica: {ec} mS/cm\n"
    ) if any(v != "N/D" for v in [humidity, temperature, ph, ec]) else "TELEMETRÍA: Sin datos de sensores en vivo.\n"

    rag_block = f"BASE DE CONOCIMIENTO LOCAL:\n{rag_context}" if rag_context else "BASE DE CONOCIMIENTO LOCAL: Sin documentos relevantes."
    trefle_block = f"DATOS BOTÁNICOS (Trefle.io):\n{trefle_context}" if trefle_context else ""

    context_section = "\n\n".join(filter(None, [iot_block, rag_block, trefle_block]))

    return f"{base}\n\nCONTEXTO DISPONIBLE:\n{context_section}"


class MoleAIChatUseCase:
    def __init__(
        self,
        llm_client: LLMClient,
        vector_store: PgVectorStore,
        redis_adapter: RedisSensorCacheAdapter,
        citation_manager: CitationManager,
        system_prompt: str,
    ):
        self.llm_client = llm_client
        self.vector_store = vector_store
        self.redis_adapter = redis_adapter
        self.citation_manager = citation_manager
        self.trefle_token = os.getenv("TREFLE_API_TOKEN", "")
        self.system_prompt = system_prompt or _BASE_SYSTEM_PROMPT

    async def _search_trefle_api(self, query: str) -> str:
        if not self.trefle_token:
            return ""
        logger.info(f"Consultando Trefle.io: '{query}'")
        url = f"https://trefle.io/api/v1/plants/search?token={self.trefle_token}&q={query}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data"):
                            p = data["data"][0]
                            return (
                                f"Nombre Científico: {p.get('scientific_name')}, "
                                f"Familia: {p.get('family_common_name', 'Desconocida')}, "
                                f"Nombre Común: {p.get('common_name', 'Desconocido')}."
                            )
        except Exception as e:
            logger.error(f"Error Trefle.io: {e}")
        return ""

    async def ainvoke(self, request: ChatRequest) -> ChatResponse:
        hashed_id = PIISanitizer.hash_user_id(request.user_id)
        logger.info("Procesando consulta RAG+CAG", extra={"user_hash": hashed_id})

        mensaje_seguro = PIISanitizer.sanitize(request.message)

        # 1. Contexto: Sensores IoT (Redis CAG) + RAG (pgvector)
        sensor_data = await self.redis_adapter.get_context(request.user_id)
        rag_context, rag_sources = await self.vector_store.asearch(mensaje_seguro)

        # 2. Fallback Trefle.io si RAG vacío
        trefle_context = ""
        if not rag_context or len(rag_context.strip()) < 10:
            trefle_context = await self._search_trefle_api(mensaje_seguro)

        # 3. Construcción del system prompt con IoT injected
        final_system_prompt = _build_system_prompt(
            base=self.system_prompt,
            sensor_data=sensor_data or {},
            rag_context=rag_context or "",
            trefle_context=trefle_context,
        )

        # 4. Inferencia NVIDIA NIM
        try:
            response = await self.llm_client.generate(
                system_prompt=final_system_prompt,
                user_message=mensaje_seguro,
            )

            has_context = bool(rag_context and len(rag_context.strip()) > 10) or bool(trefle_context)
            if not has_context:
                response.sources = []
            elif not response.sources:
                context_dict = {
                    "telemetria_sensores": sensor_data if sensor_data else "",
                    "base_conocimiento_local": rag_context,
                    "base_conocimiento_externa": trefle_context
                }
                response.sources = await self.citation_manager.extract_sources(context_dict) or []

            return response

        except Exception as e:
            logger.error("[MoleAIChatUseCase] Fallo crítico LLM", exc_info=True, extra={"user_hash": hashed_id})
            return ChatResponse(
                respuesta="Ocurrió un error de conexión con el modelo. Por favor, intenta de nuevo.",
                sources=[],
                disclaimer="AVISO LEGAL: Sistema en contingencia.",
            )