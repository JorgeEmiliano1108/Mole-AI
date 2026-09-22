"""Orquestador V3 (MRF04): Router implacable + LangGraph tras puertos.

Sin red ni LLM real: fakes por constructor. Cero imports de infrastructure.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app.application.orchestration.graph import MoleAIOrchestrator
from app.application.orchestration.router import RouterAgent, route
from app.domain.schemas import ChatRequest
from tests.fakes import FakeLLMClient, FakeVectorStore, FakeRedisAdapter


class CountingVectorStore(FakeVectorStore):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.calls = 0

    async def asearch(self, query, k=3):
        self.calls += 1
        return await super().asearch(query, k)


class CountingRedis(FakeRedisAdapter):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.calls = 0

    async def get_context(self, user_id):
        self.calls += 1
        return await super().get_context(user_id)


class BareLLM(FakeLLMClient):
    """LLM sin disclaimer: el validador debe inyectar el COFEPRIS."""

    async def generate(self, system_prompt, user_message):
        from app.domain.schemas import ChatResponse
        return ChatResponse(respuesta="corta", disclaimer="",
                            generated_by="Mole.AI")


def _orch(llm=None, vec=None, redis=None, **kw):
    return MoleAIOrchestrator(
        llm_client=llm or FakeLLMClient(respuesta="ok"),
        vector_store=vec or FakeVectorStore(search_return=("doc", [])),
        redis_adapter=redis or FakeRedisAdapter(context={}),
        **kw,
    )


class TestRouter:
    @pytest.mark.parametrize("msg,expected", [
        ("hola", "fast"),
        ("Gracias!", "fast"),
        ("", "fast"),
        ("ok", "fast"),
        ("Mi tomate tiene manchas amarillas, ¿qué hago?", "deep"),
        ("¿Cada cuánto riego? Sensor marca humedad 20%", "deep"),
        ("tizón tardío en papa: tratamiento orgánico", "deep"),
        ("cuéntame un chiste largo sobre la vida en el campo y esas cosas", "deep"),
    ])
    def test_rutas(self, msg, expected):
        assert route(msg)[0] == expected

    def test_motivo_siempre_presente(self):
        r, reason = route("hola")
        assert isinstance(reason, str) and reason


@pytest.mark.asyncio
async def test_fast_no_toca_retrieval():
    vec, redis = CountingVectorStore(), CountingRedis()
    orch = _orch(vec=vec, redis=redis)
    resp = await orch.ainvoke(ChatRequest(user_id="u", message="hola"))
    assert resp.respuesta == "ok"
    assert vec.calls == 0 and redis.calls == 0


@pytest.mark.asyncio
async def test_deep_delega_y_conserva_disclaimer():
    orch = _orch()
    resp = await orch.ainvoke(
        ChatRequest(user_id="u", message="manchas en tomate, ¿tratamiento?"))
    assert resp.respuesta == "ok"
    assert resp.disclaimer  # COFEPRIS del fake o del validador


@pytest.mark.asyncio
async def test_validador_inyecta_disclaimer():
    orch = _orch(llm=BareLLM())
    resp = await orch.ainvoke(ChatRequest(user_id="u", message="hola"))
    assert resp.disclaimer and len(resp.disclaimer) > 10


@pytest.mark.asyncio
async def test_timeout_aborta():
    import asyncio

    class SlowLLM(FakeLLMClient):
        async def generate(self, system_prompt, user_message):
            await asyncio.sleep(5)
            return await super().generate(system_prompt, user_message)

    orch = _orch(llm=SlowLLM(), timeout_s=0.05)
    with pytest.raises(TimeoutError):
        await orch.ainvoke(ChatRequest(user_id="u", message="hola"))
