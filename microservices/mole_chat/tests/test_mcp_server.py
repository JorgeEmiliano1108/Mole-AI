"""Tests unitarios del scaffold del servidor MCP.

Verifican que el servidor exponga la tool `ping` y que la tool de contexto de
sensores use correctamente el adaptador inyectado. No requieren levantar el
endpoint SSE.
"""
import pytest

from app.infrastructure.mcp.server import _call_tool, _list_tools, set_redis_adapter


class FakeRedisAdapter:
    def __init__(self, context):
        self._context = context

    async def get_context(self, user_id: str):
        return self._context


@pytest.fixture
def fake_adapter():
    return FakeRedisAdapter({"temperature": 24.5, "humidity": 60})


@pytest.mark.asyncio
async def test_mcp_list_tools_includes_ping():
    tools = await _list_tools()
    names = {t.name for t in tools}
    assert "ping" in names


@pytest.mark.asyncio
async def test_mcp_ping_tool_returns_pong():
    result = await _call_tool("ping", {})
    assert len(result) == 1
    assert result[0].text == "pong"


@pytest.mark.asyncio
async def test_mcp_unknown_tool_raises():
    with pytest.raises(ValueError, match="Tool desconocida"):
        await _call_tool("not_a_tool", {})


@pytest.mark.asyncio
async def test_mcp_get_sensor_context(fake_adapter):
    set_redis_adapter(fake_adapter)
    result = await _call_tool("get_sensor_context", {"user_id": "user-123"})
    assert "24.5" in result[0].text
    assert "60" in result[0].text


@pytest.mark.asyncio
async def test_mcp_get_sensor_context_requires_user_id():
    set_redis_adapter(FakeRedisAdapter({}))
    with pytest.raises(ValueError, match="requiere 'user_id'"):
        await _call_tool("get_sensor_context", {})


@pytest.mark.asyncio
async def test_mcp_get_sensor_context_fails_without_adapter():
    set_redis_adapter(None)
    with pytest.raises(RuntimeError, match="Redis adapter no inicializado"):
        await _call_tool("get_sensor_context", {"user_id": "user-123"})
