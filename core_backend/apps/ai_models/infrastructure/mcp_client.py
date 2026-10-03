"""Cliente MCP para Django (host) → mole_chat (servidor SSE).

Diseño:
- Rutina puramente asíncrona (`MCPChatClient.chat`) que abre una conexión SSE
  por llamada, inicializa la sesión MCP, invoca la tool `chat` y devuelve la
  respuesta.
- El consumo desde vistas/Celery sincrónicas se hace mediante
  `asgiref.sync.async_to_sync`, evitando bloquear el event loop de WSGI.
- No se mantiene pool de conexiones persistentes en el MVP: cada llamada abre
  y cierra su propia sesión SSE. Esto evita thread starvation en Gunicorn y
  simplifica el manejo de reconexiones. Un pool podría añadirse cuando el
  throughput lo justifique, usando un `WeakKeyDictionary` por thread ASGI o
  una cola de sesiones reutilizables bajo un solo loop asyncio.
"""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

from apps.ai_models.services import MoleAIServiceError

logger = logging.getLogger(__name__)


class MCPChatClient:
    """Cliente MCP para la tool `chat` expuesta por mole_chat."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        self.base_url = base_url or getattr(settings, "MCP_CHAT_URL", "http://ms2_chat:8002/mcp")
        self.timeout = timeout or getattr(settings, "MCP_TIMEOUT", 60)

    async def chat(
        self,
        *,
        user_id: str,
        message: str,
        session_id: str | None = None,
        plant_id: str | None = None,
    ) -> dict[str, Any]:
        """Invoca la tool `chat` del servidor MCP y devuelve un dict plano.

        El dict contiene al menos: respuesta, sources, disclaimer, blocked.
        """
        sse_url = f"{self.base_url}/v1/sse"
        tool_arguments: dict[str, Any] = {
            "user_id": user_id,
            "message": message,
        }
        if session_id:
            tool_arguments["session_id"] = session_id
        if plant_id:
            tool_arguments["plant_id"] = plant_id

        try:
            async with sse_client(url=sse_url, timeout=self.timeout) as (
                read_stream,
                write_stream,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(
                        "chat",
                        arguments=tool_arguments,
                    )
                    return _parse_tool_result(result)
        except Exception as exc:  # noqa: BLE001
            logger.warning("MCP chat call failed: %s", exc)
            raise MoleAIServiceError(f"MCP chat call failed: {exc}") from exc


def _parse_tool_result(result: Any) -> dict[str, Any]:
    """Normaliza el resultado de una tool MCP a un dict Python."""
    if isinstance(result, dict):
        return result
    # El SDK suele devolver un objeto con atributo `content` (lista de TextContent).
    content = getattr(result, "content", None)
    if content and isinstance(content, list):
        texts = [getattr(item, "text", str(item)) for item in content]
        combined = "\n".join(texts)
        try:
            import json

            return json.loads(combined)
        except json.JSONDecodeError:
            return {"respuesta": combined, "sources": [], "disclaimer": "", "blocked": False}
    return {"respuesta": str(result), "sources": [], "disclaimer": "", "blocked": False}
