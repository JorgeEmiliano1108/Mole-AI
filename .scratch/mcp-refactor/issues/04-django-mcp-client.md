# 04: A4: Adaptador MCP cliente en Django (MoleAIClient)

Status: ready-for-agent

## Requisito

Extender `core_backend/apps/ai_models/services.py::MoleAIClient` para soportar MCP como transporte alternativo a REST, controlado por feature flag.

## Acceptance criteria

- [ ] Nuevo adaptador `MCPChatClient` en `apps/ai_models/infrastructure/mcp_client.py`.
- [ ] `MoleAIClient` delega a `MCPChatClient` cuando `settings.MCP_ENABLED` es True; REST en caso contrario.
- [ ] Circuit breaker reutilizado en la rama MCP.
- [ ] Timeout y reintentos configurables (`MCP_TIMEOUT`, `MCP_RETRIES`).
- [ ] Manejo de fallo graceful: si MCP falla, fallback a REST.
- [ ] Tests unitarios con servidor MCP fake.

## Blocked by

- `03-mcp-tools-resources`.

## Notas

Patrón Adapter/Strategy. No se cambia la interfaz pública del cliente.

