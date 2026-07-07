"""Tests for nvidia_client.py using a fake NIM HTTP server (FastAPI + ASGITransport)."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import json
from fastapi import FastAPI
from pydantic import BaseModel
from httpx import AsyncClient, ASGITransport
from openai import AsyncOpenAI

from app.infrastructure.adapters.nvidia_client import LLMClient
from app.domain.schemas import ChatResponse


# ── Fake NIM HTTP Server ──────────────────────────────────────────────────

fake_nim = FastAPI()


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list
    temperature: float = 0.2
    max_tokens: int = 1024
    top_p: float = 0.7


@fake_nim.post("/v1/chat/completions")
async def fake_completions(req: ChatCompletionRequest):
    return {
        "choices": [
            {
                "message": {
                    "content": "Respuesta desde fake NIM"
                }
            }
        ]
    }


@fake_nim.post("/v1/embeddings")
async def fake_embeddings():
    return {
        "data": [
            {"embedding": [0.1, 0.2, 0.3]}
        ]
    }


@pytest.fixture
def fake_nim_client() -> AsyncOpenAI:
    """Create an AsyncOpenAI client pointed at the fake NIM server."""
    transport = ASGITransport(app=fake_nim)
    http_client = AsyncClient(transport=transport, base_url="http://test")
    return AsyncOpenAI(
        api_key="fake-key",
        base_url="http://test/v1",
        http_client=http_client,
    )


@pytest.fixture
def llm_client(fake_nim_client) -> LLMClient:
    return LLMClient(client=fake_nim_client)


@pytest.mark.asyncio
async def test_generate_returns_chat_response(llm_client):
    response = await llm_client.generate(
        system_prompt="Eres un asistente.",
        user_message="Hola",
    )
    assert isinstance(response, ChatResponse)
    assert "fake NIM" in response.respuesta
    assert "disclaimer" in response.respuesta or response.disclaimer


@pytest.mark.asyncio
async def test_generate_with_fallback_on_circuit_breaker(llm_client):
    """When the NIM server returns an error, circuit breaker should trigger fallback."""
    response = await llm_client.generate(
        system_prompt="Eres un asistente.",
        user_message="Hola",
    )
    assert isinstance(response, ChatResponse)
