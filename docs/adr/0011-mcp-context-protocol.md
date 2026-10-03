# ADR-0011: Model Context Protocol (MCP) como protocolo de contexto Django ↔ mole_chat

- **Fecha:** 2026-10-02
- **Estado:** Aceptado (supera parcialmente ADR-0008 §3 punto MCP)
- **Contexto:** La auditoría de trazabilidad (`.scratch/traceabilidad/PRD.md`) identificó que RF-AI-03 exige MCP, pero el código implementa REST stateless entre Django y `mole_chat`. Esta decisión establece la transición controlada a MCP sin romper la API pública móvil ni el bajo acoplamiento alcanzado.

## 1. Decisión

1. **Se adopta MCP** como protocolo de contexto para el canal interno **Django (host) ↔ `microservices/mole_chat` (servidor MCP)**.
2. **Transporte:** Streamable HTTP/SSE (Server-Sent Events). No se usa stdio porque ambos servicios corren en contenedores Docker separados.
3. **SDK oficial:** `mcp>=1.0` en Python; no se reinventa JSON-RPC.
4. **API pública móvil:** se mantiene REST según `docs/mobile-contract.md` y `docs/contracts/openapi.yml`. El cambio es transparente para la app Flutter.
5. **`mole_vision` queda fuera del MVP como servidor MCP**, pero el host se diseña para poder registrar una tool futura (`analyze_image`) sin reescribir el cliente.
6. **REST interno se mantiene como fallback** mientras el feature flag `MCP_ENABLED` esté activo (patrón Strangler Fig).
7. **SafetyValidator y AuditLog inmutable se mantienen** como gates fail-closed, aplicados tanto a resultados de tools como a la respuesta final del LLM.

## 2. Consecuencias

- **Positivas:**
  - El LLM puede solicitar dinámicamente contexto (historial, telemetría, diagnósticos previos) en lugar de depender de un prompt ensamblado manualmente en Django.
  - Se desacopla la lógica de contexto del cliente HTTP: las tools/resources viven en `mole_chat`.
  - Se facilita la extensión agéntica futura (`mole_vision` como tool, nuevos sensores, etc.).
- **Negativas / Riesgos:**
  - Aumenta la complejidad operativa: hay que mantener endpoint SSE, timeouts, reconexiones y circuit breaker.
  - Requiere suite de paridad REST-vs-MCP antes de activar en producción.
  - El SDK `mcp` es relativamente nuevo; se fija versión mayor (`>=1.0,<2.0`) para reducir drift.

## 3. Componentes afectados

- `microservices/mole_chat/app/infrastructure/mcp/` (nuevo)
- `microservices/mole_chat/app/main.py` (montar endpoint SSE)
- `core_backend/apps/ai_models/infrastructure/mcp_client.py` (nuevo)
- `core_backend/apps/ai_models/services.py::MoleAIClient` (rama MCP)
- `microservices/mole_chat/app/application/orchestration/graph.py` (nodo tools)
- `.env` / settings: `MCP_ENABLED`, `MCP_CHAT_URL`, `MCP_TIMEOUT`, `MCP_RETRIES`

## 4. Cumplimiento normativo

- **LFPDPPP:** el contexto dinámico puede contener datos personales/sensibles. Las tools deben aplicar el mismo principio de minimización (solo solicitar `plant_id`/`user_id` necesarios) y el historial se sigue almacenando con `session_id` + TTL.
- **NOM-059 / COFEPRIS / NIST AI RMF:** `SafetyValidator` actúa como gate de salida y, además, se valida el resultado de cada tool antes de inyectarlo al contexto del LLM. Los bloqueos se registran en `AuditLog` append-only.

## 5. Relación con otros ADRs

- **ADR-0004** (proveedores NVIDIA/OpenWeather): se mantiene; MCP no sustituye al proveedor LLM, solo al transporte de contexto.
- **ADR-0008** (brechas metodológicas): se supera parcialmente. El punto "MCP → REST+NVIDIA" se resuelve implementando MCP; los puntos CRDTs y Web Mining quedan fuera del MVP según decisión ejecutiva.
- **ADR-0010** (safety gate en chat RAG): se mantiene; el safety gate se aplica también a resultados de tools MCP.

## 6. Métricas de éxito

- Suite de paridad REST-vs-MCP verde.
- Latencia del canal MCP no mayor al 110 % de la ruta REST en ambiente de laboratorio.
- 100 % de tests red-team sobre agroquímicos/especies protegidas pasan vía MCP.
