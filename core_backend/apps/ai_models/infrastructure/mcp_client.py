"""Cliente MCP para Django (host) → mole_chat (servidor SSE).

El cliente es un wrapper síncrono sobre MCPConnectionPool, que mantiene sesiones
SSE persistentes en un daemon thread y multiplexa llamadas JSON-RPC por id.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from apps.ai_models.services import MoleAIServiceError

from .mcp_pool import MCPConnectionPool

logger = logging.getLogger(__name__)


class MCPChatClient:
    """Cliente MCP para la tool `chat` expuesta por mole_chat."""

    def __init__(self, pool: MCPConnectionPool | None = None):
        self._pool = pool or MCPConnectionPool()

    def chat(
        self,
        *,
        user_id: str,
        message: str,
        session_id: str | None = None,
        plant_id: str | None = None,
    ) -> dict[str, Any]:
        """Invoca la tool `chat` del servidor MCP y devuelve un dict plano."""
        tool_arguments: dict[str, Any] = {
            "user_id": user_id,
            "message": message,
        }
        if session_id:
            tool_arguments["session_id"] = session_id
        if plant_id:
            tool_arguments["plant_id"] = plant_id

        try:
            result = self._pool.call_tool("chat", tool_arguments)
            return _parse_tool_result(result)
        except Exception as exc:  # noqa: BLE001
            logger.warning("MCP chat call failed: %s", exc)
            raise MoleAIServiceError(f"MCP chat call failed: {exc}") from exc


def _parse_tool_result(result: Any) -> dict[str, Any]:
    """Normaliza el resultado de una tool MCP a un dict Python."""
    if isinstance(result, dict):
        return result
    content = getattr(result, "content", None)
    if content and isinstance(content, list):
        texts = [getattr(item, "text", str(item)) for item in content]
        combined = "\n".join(texts)
        try:
            return json.loads(combined)
        except json.JSONDecodeError:
            return {"respuesta": combined, "sources": [], "disclaimer": ""}
    return {"respuesta": str(result), "sources": [], "disclaimer": ""}
