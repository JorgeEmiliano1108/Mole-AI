"""Scaffold del servidor MCP para mole_chat.

Expone un endpoint SSE bajo /mcp/v1/sse y un endpoint POST para mensajes.
Por ahora registra:
- ping: health-check del servidor MCP.
- get_sensor_context: lectura del contexto de sensores almacenado en Redis.
Las tools reales de contexto dinámico (diagnósticos históricos, telemetría
granular, etc.) se añaden en iteraciones posteriores.
"""
from __future__ import annotations

import logging
from typing import Any

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.routing import Route

logger = logging.getLogger(__name__)

# Servidor MCP con nombre canónico. Se importa explícitamente para tests.
mcp_server = Server("mole_chat")

# Dependencia inyectada desde el lifespan de FastAPI.
_redis_adapter: Any | None = None


def set_redis_adapter(adapter: Any) -> None:
    """Inyecta el adaptador de caché de sensores usado por las tools MCP."""
    global _redis_adapter
    _redis_adapter = adapter


@mcp_server.list_tools()
async def _list_tools() -> list[Tool]:
    """Herramientas disponibles para el host MCP."""
    return [
        Tool(
            name="ping",
            description="Health check del servidor MCP.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_sensor_context",
            description="Obtiene el contexto de sensores más reciente para un usuario.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Identificador del usuario (UUID o ID interno).",
                    },
                },
                "required": ["user_id"],
            },
        ),
    ]


@mcp_server.call_tool()
async def _call_tool(name: str, arguments: dict | None = None) -> list[TextContent]:
    """Dispatcher de invocación de tools."""
    arguments = arguments or {}

    if name == "ping":
        return [TextContent(type="text", text="pong")]

    if name == "get_sensor_context":
        user_id = arguments.get("user_id")
        if not user_id:
            raise ValueError("get_sensor_context requiere 'user_id'")
        if _redis_adapter is None:
            raise RuntimeError("Redis adapter no inicializado")
        context = await _redis_adapter.get_context(str(user_id))
        return [TextContent(type="text", text=str(context))]

    raise ValueError(f"Tool desconocida: {name}")


def create_mcp_app() -> Starlette:
    """Factory de la sub-aplicación ASGI que expone el transporte SSE."""
    sse = SseServerTransport("/mcp/v1/sse/messages/")

    async def handle_sse(request):
        async with sse.connect_session(
            request.scope, request.receive, request._send
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    async def handle_messages(request):
        await sse.handle_post_message(
            request.scope, request.receive, request._send
        )

    return Starlette(
        routes=[
            Route("/mcp/v1/sse", endpoint=handle_sse),
            Route(
                "/mcp/v1/sse/messages/",
                endpoint=handle_messages,
                methods=["POST"],
            ),
        ],
    )
