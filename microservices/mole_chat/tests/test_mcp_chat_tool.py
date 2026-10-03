"""Tests de la tool `chat` del servidor MCP.

No requieren levantar el endpoint SSE; prueban directamente el dispatcher de
tools con adaptadores falsos.
"""
import json

import pytest

from app.infrastructure.mcp.server import _call_tool, _list_tools, set_chat_adapter


class FakeChatAdapter:
    def __init__(self, response):
        self._response = response
        self.calls = []

    async def chat(self, *, user_id, message, session_id=None, plant_id=None):
        self.calls.append({
            "user_id": user_id,
            "message": message,
            "session_id": session_id,
            "plant_id": plant_id,
        })
        return self._response


@pytest.fixture
def safe_adapter():
    adapter = FakeChatAdapter({
        "respuesta": "Usa compostaje.",
        "sources": [{"autor": "Test", "url": "http://test", "confianza": 0.95}],
        "disclaimer": "Aviso legal.",
        "generated_by": "Mole.AI",
        "blocked": False,
        "block_code": "",
        "block_reason": "",
    })
    set_chat_adapter(adapter)
    return adapter


@pytest.fixture
def blocked_adapter():
    adapter = FakeChatAdapter({
        "respuesta": "",
        "sources": [],
        "disclaimer": "Aviso legal.",
        "generated_by": "Mole.AI",
        "blocked": True,
        "block_code": "SAFETY_NOM059_PROTECTED",
        "block_reason": "Especie protegida.",
    })
    set_chat_adapter(adapter)
    return adapter


@pytest.mark.asyncio
async def test_mcp_list_tools_includes_chat():
    tools = await _list_tools()
    names = {t.name for t in tools}
    assert "chat" in names


@pytest.mark.asyncio
async def test_mcp_chat_tool_returns_json_payload(safe_adapter):
    result = await _call_tool("chat", {
        "user_id": "user-42",
        "message": "¿cómo fertilizo?",
        "session_id": "session-1",
        "plant_id": "plant-7",
    })
    assert len(result) == 1
    payload = json.loads(result[0].text)
    assert payload["respuesta"] == "Usa compostaje."
    assert payload["blocked"] is False
    assert payload["sources"][0]["autor"] == "Test"
    assert safe_adapter.calls == [{
        "user_id": "user-42",
        "message": "¿cómo fertilizo?",
        "session_id": "session-1",
        "plant_id": "plant-7",
    }]


@pytest.mark.asyncio
async def test_mcp_chat_tool_returns_blocked_payload(blocked_adapter):
    result = await _call_tool("chat", {
        "user_id": "user-42",
        "message": "¿dónde vendo biznagas?",
    })
    payload = json.loads(result[0].text)
    assert payload["blocked"] is True
    assert payload["block_code"] == "SAFETY_NOM059_PROTECTED"


@pytest.mark.asyncio
async def test_mcp_chat_requires_user_id_and_message():
    set_chat_adapter(FakeChatAdapter({}))
    with pytest.raises(ValueError, match="chat requiere"):
        await _call_tool("chat", {"user_id": "user-42"})


@pytest.mark.asyncio
async def test_mcp_chat_fails_without_adapter():
    set_chat_adapter(None)
    with pytest.raises(RuntimeError, match="Chat adapter no inicializado"):
        await _call_tool("chat", {"user_id": "user-42", "message": "hola"})
