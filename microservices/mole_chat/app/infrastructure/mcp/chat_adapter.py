"""Adaptador para invocar el caso de uso de chat desde el servidor MCP.

Orquesta: sanitizar pregunta (PII), ejecutar RAG+LLM, validar salida contra
el SafetyValidator de Django y devolver un dict serializable para MCP.
"""
from __future__ import annotations

import logging
from typing import Any

from app.application.use_cases.chat_usecase import MoleAIChatUseCase
from app.domain.protocols import LLMClientPort, VectorStorePort, RedisAdapterPort, CitationManagerPort
from app.domain.schemas import ChatRequest, ChatResponse, COFEPRIS_DISCLAIMER
from app.infrastructure.adapters.prompt_loader import load_prompt
from app.infrastructure.adapters.safety_client import SafetyClient

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
        safety_client: SafetyClient,
    ):
        self.redis_adapter = redis_adapter
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.citation_manager = citation_manager
        self.safety_client = safety_client

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

        # Fail-closed: validar salida del LLM contra SafetyValidator de Django.
        safety = await self.safety_client.validate(response.respuesta, user_id=user_id)
        if not safety.safe:
            logger.warning(
                "MCP chat safety block",
                code=safety.code,
                reason=safety.reason,
                user_id=user_id,
            )
            return {
                "respuesta": (
                    "No puedo proporcionar esa información porque podría violar "
                    "nuestras políticas de seguridad o normativa ambiental aplicable."
                ),
                "sources": [],
                "disclaimer": COFEPRIS_DISCLAIMER,
                "generated_by": "Mole.AI",
                "blocked": True,
                "block_code": safety.code,
                "block_reason": safety.reason,
            }

        return {
            "respuesta": response.respuesta,
            "sources": [s.model_dump() for s in response.sources],
            "disclaimer": COFEPRIS_DISCLAIMER,
            "generated_by": response.generated_by,
            "blocked": False,
            "block_code": "",
            "block_reason": "",
        }
