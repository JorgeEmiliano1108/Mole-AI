"""Adaptador para invocar el caso de uso de chat desde el servidor MCP.

Orquesta: sanitizar pregunta (PII), ejecutar RAG+LLM y devolver un dict
serializable para MCP. La validación de seguridad vive en el host Django
(middleware de salida), no aquí.
"""
from __future__ import annotations

import logging
from typing import Any

from app.application.use_cases.chat_usecase import MoleAIChatUseCase
from app.domain.protocols import LLMClientPort, VectorStorePort, RedisAdapterPort, CitationManagerPort
from app.domain.schemas import ChatRequest, ChatResponse, COFEPRIS_DISCLAIMER
from app.infrastructure.adapters.prompt_loader import load_prompt

logger = logging.getLogger(__name__)


class MCPChatAdapter:
    """Adaptador que conecta el servidor MCP con el caso de uso de chat."""

    def __init__(
        self,
        *,
        redis_adapter: RedisAdapterPort,
        vector_store: VectorStorePort,
        llm_client: LLMClientPort,
        citation_manager: CitationManagerPort,
    ):
        self.redis_adapter = redis_adapter
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.citation_manager = citation_manager

    async def chat(
        self,
        *,
        user_id: str,
        message: str,
        session_id: str | None = None,
        plant_id: str | None = None,
    ) -> dict[str, Any]:
        """Ejecuta la consulta y devuelve un dict con respuesta, sources, etc."""
        try:
            system_prompt = load_prompt("agronomist")
        except Exception:  # noqa: BLE001
            system_prompt = "Eres Mole.AI, un asistente agrónomo experto especializado en flora."

        request = ChatRequest(user_id=user_id, message=message, session_id=session_id)

        use_case = MoleAIChatUseCase(
            llm_client=self.llm_client,
            vector_store=self.vector_store,
            redis_adapter=self.redis_adapter,
            citation_manager=self.citation_manager,
            system_prompt=system_prompt,
        )

        response: ChatResponse = await use_case.ainvoke(request)

        return {
            "respuesta": response.respuesta,
            "sources": [s.model_dump() for s in response.sources],
            "disclaimer": COFEPRIS_DISCLAIMER,
            "generated_by": response.generated_by,
        }
