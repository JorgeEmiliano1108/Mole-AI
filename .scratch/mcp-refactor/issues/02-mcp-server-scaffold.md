# 02: A2: Scaffold del servidor MCP en mole_chat (Streamable HTTP/SSE)

Status: ready-for-agent

## Requisito

Agregar `mcp` SDK oficial a `microservices/mole_chat` y exponer un servidor MCP montado en el router FastAPI existente con transporte Streamable HTTP/SSE.

## Acceptance criteria

- [ ] `mcp>=1.0` añadido a `microservices/mole_chat/requirements.txt`.
- [ ] Módulo `app/infrastructure/mcp/server.py` con `mcp.Server("mole_chat")` y configuración de transporte SSE.
- [ ] Endpoint `/mcp/v1/sse` registrado en `app/main.py` sin romper rutas existentes.
- [ ] Health check del servidor MCP disponible.
- [ ] Tests unitarios del servidor con cliente fake.

## Blocked by

- `01-adr-mcp` (aprobación del ADR).

## Notas

Usar feature flag `MCP_ENABLED` para no activar el endpoint en producción hasta que haya paridad.

## Comments

**2026-10-02 — opencode**
Implementado:
- `mcp>=1.0,<2.0` añadido a `microservices/mole_chat/requirements.txt`.
- `app/core/config.py`: `MCP_ENABLED: bool = False`.
- `app/infrastructure/mcp/server.py`: servidor MCP con tool `ping` y transporte SSE (`/mcp/v1/sse`, `/mcp/v1/sse/messages/`).
- `app/api/main.py`: montaje condicional bajo `/mcp` cuando `MCP_ENABLED=True`.
- `tests/test_mcp_server.py`: 3 tests unitarios pasan (`pytest tests/test_mcp_server.py`).

 Pendiente: regenerar `requirements.lock` con `pip-compile` antes del build Docker.

