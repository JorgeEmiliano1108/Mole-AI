"""Servidor MCP para mole_chat.

Expone un endpoint SSE bajo /mcp/v1/sse y un endpoint POST para mensajes.
Tools:
- ping: health-check del servidor MCP.
- get_sensor_context: lectura del contexto de sensores almacenado en Redis.
- chat: caso de uso RAG+CAG+LLM con validación fail-closed vía SafetyValidator.
"""
from __future__ import annotations

import json
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

# Dependencias inyectadas desde el lifespan de FastAPI.
_redis_adapter: Any | None = None
_chat_adapter: Any | None = None


def set_redis_adapter(adapter: Any) -> None:
    """Inyecta el adaptador de caché de sensores usado por las tools MCP."""
    global _redis_adapter
    _redis_adapter = adapter


def set_chat_adapter(adapter: Any) -> None:
    """Inyecta el adaptador que ejecuta el caso de uso de chat."""
    global _chat_adapter
    _chat_adapter = adapter


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
        Tool(
            name="chat",
            description="Responde una pregunta agronómica usando RAG, contexto de sensores y LLM. "
                        "La salida del LLM es validada por el SafetyValidator antes de devolverse.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Identificador del usuario.",
                    },
                    "message": {
                        "type": "string",
                        "description": "Pregunta del usuario.",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "ID de sesión de chat (opcional).",
                    },
                    "plant_id": {
                        "type": "string",
                        "description": "ID de planta/sitio (opcional).",
                    },
                },
                "required": ["user_id", "message"],
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

    if name == "chat":
        if _chat_adapter is None:
            raise RuntimeError("Chat adapter no inicializado")
        user_id = arguments.get("user_id")
        message = arguments.get("message")
        if not user_id or not message:
            raise ValueError("chat requiere 'user_id' y 'message'")
        result = await _chat_adapter.chat(
            user_id=str(user_id),
            message=str(message),
            session_id=arguments.get("session_id"),
            plant_id=arguments.get("plant_id"),
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    raise ValueError(f"Tool desconocida: {name}")


def create_mcp_app() -> Starlette:
    """Factory de la sub-aplicación ASGI que expone el transporte SSE.

    Nota: las rutas NO llevan el prefijo /mcp; ese prefijo se añade al hacer
    `app.mount("/mcp", create_mcp_app())` en `main.py`. El endpoint visible
    final es `/mcp/v1/sse`.
    """
    sse = SseServerTransport("/v1/sse/messages/")

    class _SSEEndpoint:
        async def __call__(self, scope, receive, send):
            async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )

    class _MessagesEndpoint:
        async def __call__(self, scope, receive, send):
            await sse.handle_post_message(scope, receive, send)

    return Starlette(
        routes=[
            Route("/v1/sse", endpoint=_SSEEndpoint()),
            Route(
                "/v1/sse/messages/",
                endpoint=_MessagesEndpoint(),
                methods=["POST"],
            ),
        ],
    )
