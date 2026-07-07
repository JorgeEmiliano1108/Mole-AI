"""Tests for MoleAIChatUseCase — uses hand-written fakes injected via constructor."""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.application.use_cases.chat_usecase import MoleAIChatUseCase
from app.domain.schemas import ChatRequest, ChatResponse
from tests.fakes import FakeLLMClient, FakeVectorStore, FakeRedisAdapter


@pytest.fixture
def use_case():
    redis_adapter = FakeRedisAdapter(context={"context": "Temp: 25C, Humedad: 60%"})
    vector_store = FakeVectorStore(search_return=("Documento sobre tomates.", []))
    llm_client = FakeLLMClient(respuesta="El tomate está bien.")
    return MoleAIChatUseCase(
        redis_adapter=redis_adapter,
        vector_store=vector_store,
        llm_client=llm_client,
        system_prompt="Eres un asistente agrícola.",
    )


@pytest.mark.asyncio
async def test_usecase_orchestration_success(use_case):
    request = ChatRequest(user_id="test_user_123", message="Hola Mole")
    response = await use_case.ainvoke(request)
    assert response.respuesta == "El tomate está bien."
    assert "AVISO LEGAL" in response.disclaimer or response.disclaimer
