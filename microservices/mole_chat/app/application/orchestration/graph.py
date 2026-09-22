"""Orquestador LangGraph tras puertos (V3, MRF04, hexagonal estricto).

El grafo solo conoce PUERTOS (`LLMClientPort`, `VectorStorePort`,
`RedisAdapterPort`, `CitationManagerPort`) y el caso de uso existente
(`MoleAIChatUseCase`) para el camino profundo. Ningún import de
`infrastructure`/`adapters` aquí: violarlo rompe el gate.

Topología: route → fast | deep → validate → END.
- fast: 1 llamada LLM con prompt compacto (cero retrieval, cero Redis).
- deep: delega íntegro a `MoleAIChatUseCase.ainvoke` (RAG + sensores + REGLA).
- validate: garantiza disclaimer no vacío (COFEPRIS por defecto).
- Timeout global configurable (defense del SLO; RNF01 3s exige streaming,
  futuro — hoy el default iguala `LLM_REQUEST_TIMEOUT`).
"""
from __future__ import annotations

import asyncio
import time
from typing import TypedDict

import structlog
from langgraph.graph import END, StateGraph

from app.application.orchestration.router import RouterAgent
from app.application.use_cases.chat_usecase import MoleAIChatUseCase
from app.domain.protocols import (
    CitationManagerPort,
    LLMClientPort,
    RedisAdapterPort,
    VectorStorePort,
)
from app.domain.schemas import ChatRequest, ChatResponse, COFEPRIS_DISCLAIMER

logger = structlog.get_logger()


class GraphState(TypedDict, total=False):
    request: ChatRequest
    route: str
    route_reason: str
    response: ChatResponse


class MoleAIOrchestrator:
    """Fachada del grafo. Construir una vez (routers) o por test con fakes."""

    def __init__(
        self,
        *,
        redis_adapter: RedisAdapterPort,
        vector_store: VectorStorePort,
        llm_client: LLMClientPort,
        citation_manager: CitationManagerPort | None = None,
        system_prompt: str | None = None,
        router: RouterAgent | None = None,
        timeout_s: float = 30.0,
    ):
        self._use_case = MoleAIChatUseCase(
            redis_adapter=redis_adapter,
            vector_store=vector_store,
            llm_client=llm_client,
            citation_manager=citation_manager,
            system_prompt=system_prompt,
        )
        self._llm_client = llm_client
        self._router = router or RouterAgent()
        self._timeout_s = timeout_s
        self._graph = self._build()

    # ── nodos (métodos puros sobre el estado; sin I/O directo) ──
    async def _node_route(self, state: GraphState) -> dict:
        route, reason = self._router.classify(state["request"].message)
        logger.info("orch_route", route=route, reason=reason)
        return {"route": route, "route_reason": reason}

    async def _node_fast(self, state: GraphState) -> dict:
        req = state["request"]
        resp = await self._llm_client.generate(
            "Eres Mole.AI, asistente agrónomo. Responde breve y en español.",
            req.message,
        )
        return {"response": resp}

    async def _node_deep(self, state: GraphState) -> dict:
        resp = await self._use_case.ainvoke(state["request"])
        return {"response": resp}

    async def _node_validate(self, state: GraphState) -> dict:
        resp = state["response"]
        if not (resp.disclaimer or "").strip():
            resp.disclaimer = COFEPRIS_DISCLAIMER
        return {"response": resp}

    def _build(self):
        g = StateGraph(GraphState)
        g.add_node("route", self._node_route)
        g.add_node("fast", self._node_fast)
        g.add_node("deep", self._node_deep)
        g.add_node("validate", self._node_validate)
        g.set_entry_point("route")
        g.add_conditional_edges(
            "route",
            lambda s: s["route"],
            {"fast": "fast", "deep": "deep"},
        )
        g.add_edge("fast", "validate")
        g.add_edge("deep", "validate")
        g.add_edge("validate", END)
        return g.compile()

    async def ainvoke(self, request: ChatRequest) -> ChatResponse:
        """Ejecuta el grafo con timeout. Lanza TimeoutError si excede."""
        t0 = time.monotonic()
        try:
            out = await asyncio.wait_for(
                self._graph.ainvoke({"request": request}),
                timeout=self._timeout_s,
            )
        except asyncio.TimeoutError as exc:
            logger.warning("orch_timeout", timeout_s=self._timeout_s)
            raise TimeoutError(
                f"Orquestador excedió {self._timeout_s}s"
            ) from exc
        ms = (time.monotonic() - t0) * 1000
        logger.info("orch_done", route=out.get("route"),
                    ms=round(ms, 1))
        return out["response"]
