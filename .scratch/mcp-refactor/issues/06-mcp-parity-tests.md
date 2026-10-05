# 06: A6: Tests de paridad REST vs MCP y validación de contrato móvil

Status: completed

## Requisito

Demostrar que el cambio de transporte interno no afecta el comportamiento observable por la app móvil.

## Acceptance criteria

- [x] Suite parametrizada que ejecuta los mismos escenarios con `MCP_ENABLED=True` y `False`.
- [x] Comparación de `ChatResponse` (ruta, disclaimer, bloqueos de seguridad).
- [x] Tests de contrato móvil (`/api/v1/ai/chat/`) pasan sin modificaciones.
- [x] Cobertura de timeout/red y safety block (NOM-059, agroquímico).

## Blocked by

- `05-mcp-safety-gate`.

## Notas

- 2026-10-04 (agente): agregado `core_backend/apps/core/tests/test_chat_mcp_parity.py` con 7 casos (safe, NOM-059 block, agro block ×2 modos + fallback REST ante fallo MCP). Gate `canonical-openapi.py` sigue verde.
- Esta suite es la condición de activación del feature flag en producción; el flip (issue 07) permanece `ready-for-human`.

