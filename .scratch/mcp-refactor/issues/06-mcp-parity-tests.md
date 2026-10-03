# 06: A6: Tests de paridad REST vs MCP y validación de contrato móvil

Status: ready-for-agent

## Requisito

Demostrar que el cambio de transporte interno no afecta el comportamiento observable por la app móvil.

## Acceptance criteria

- [ ] Suite parametrizada que ejecuta los mismos escenarios con `MCP_ENABLED=True` y `False`.
- [ ] Comparación de `ChatResponse` (ruta, disclaimer, bloqueos de seguridad).
- [ ] Tests de contrato móvil (`/api/v1/ai/chat/`) pasan sin modificaciones.
- [ ] Cobertura de ruta `fast`, `deep`, timeout y safety block.

## Blocked by

- `05-mcp-safety-gate`.

## Notas

Esta suite es la condición de activación del feature flag en producción.

