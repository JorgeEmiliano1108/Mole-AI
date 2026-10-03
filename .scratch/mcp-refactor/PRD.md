# PRD — Refactor a Model Context Protocol (MCP) Django ↔ mole_chat

**Feature:** `mcp-refactor`  
**Fecha:** 2026-10-02  
**Estado:** Aprobado por directriz ejecutiva.  
** Alcance:** Exclusivo canal Django (host) ↔ `microservices/mole_chat` (servidor MCP) vía Streamable HTTP/SSE. La API pública móvil y el contrato `docs/mobile-contract.md` **no cambian**. `mole_vision` queda fuera del MVP como servidor MCP, pero el diseño debe permitir exponerlo como `tool` futuro sin reescribir el host.

---

## Problem Statement

El sistema actual usa REST stateless entre Django y `mole_chat`. Cada request de chat debe empaquetar manualmente el historial y los últimos datos de sensor (`SensorDataAggregator.get_latest_sensor_readings`) en el prompt. Esto:
- Rompe el principio de preservación de contexto dinámico exigido por RF-AI-03.
- Acopla la lógica de ensamblaje de contexto al cliente HTTP.
- Dificulta que el LLM decida qué información adicional necesita (por ejemplo, historial de diagnósticos o telemetría de más horas).

## Solution

Introducir **Model Context Protocol (MCP)** como capa de orquestación entre Django y `mole_chat`:
- Django actúa como **MCP host/client**.
- `mole_chat` expone un **MCP server** sobre transporte Streamable HTTP/SSE.
- El servidor publica **tools** (`latest_readings`, `get_diagnosis_context`) y **resources** (`session://{user_id}/history`) que el LLM puede solicitar dinámicamente.
- El orquestador LangGraph existente (`MoleAIOrchestrator`) se extiende para invocar tools MCP antes de generar la respuesta.
- REST se mantiene como fallback detrás de un **feature flag** (`MCP_ENABLED`) durante la transición (Strangler Fig).

## User Stories

1. Como backend de Mole.AI, quiero que `mole_chat` exponga sus capacidades mediante MCP, para que el LLM negocie dinámicamente el contexto que necesita.
2. Como arquitecto, quiero un feature flag que permita alternar entre REST y MCP sin redeploy, para reducir riesgo en producción.
3. Como desarrollador, quiero que el SafetyValidator actúe también a nivel de tool call, para no relajar el cumplimiento normativo al cambiar de protocolo.
4. Como tester, quiero tests de paridad REST-vs-MCP, para garantizar que la API móvil no se rompe.
5. Como arquitecto, quiero que el diseño permita añadir `mole_vision` como tool futura sin reescribir el host, para escalar la orquestación agéntica.

## Implementation Decisions

- **SDK oficial:** `mcp>=1.0` en Python para servidor y cliente. No se reinventa JSON-RPC.
- **Transporte:** Streamable HTTP/SSE (no stdio) porque los servicios corren en contenedores Docker separados.
- **Ubicación del servidor:** dentro de `microservices/mole_chat/app/infrastructure/mcp/`, montado en el router FastAPI existente.
- **Tools iniciales:**
  - `latest_readings(plant_id: str, hours_back: int = 24) -> dict` — reutiliza `SensorDataAggregator`.
  - `get_diagnosis_context(plant_id: str, limit: int = 5) -> list[dict]` — lee `AIDiagnostic` filtrados.
- **Resources iniciales:**
  - `session://{user_id}/history` — lectura desde `redis_session_store.py` / `LLMRequest`.
- **Patrones:**
  - **Adapter:** `MoleAIClient` gana rama MCP manteniendo interfaz actual.
  - **Feature Flag:** `settings.MCP_ENABLED` y `MCP_CHAT_URL`.
  - **Circuit Breaker:** reutilizar `circuit_breaker.py` en la rama MCP.
  - **Facade:** `MoleAIOrchestrator` LangGraph ya existente; se le añade nodo `tools`.
  - **Fail-closed:** `SafetyValidator` se aplica al resultado de cada tool y a la respuesta final.
- **Compatibilidad:** la API pública `/api/v1/ai/chat/` sigue siendo REST; solo el backend-interno cambia de transporte.

## Testing Decisions

- **Paridad:** suite parametrizada que ejecuta el mismo escenario por REST y por MCP y compara `ChatResponse`.
- **Unit tests:** servidor MCP con cliente fake; verifica que tools/resources devuelven la forma esperada.
- **Contract tests:** `openapi.yml` no se modifica; tests de integración contra `/api/v1/ai/chat/`.
- **Normativos:** tests red-team aseguran que preguntas sobre agroquímicos/especies protegidas siguen siendo bloqueadas vía MCP.

## Out of Scope

- Cambiar el contrato móvil (`docs/mobile-contract.md`, `docs/contracts/openapi.yml`).
- Convertir `mole_vision` a servidor MCP en este MVP (solo se deja hook preparado).
- Modificar ESP32, edge_node ni Store-and-Forward.

## Further Notes

- ADR-0011 documentará la decisión y su relación con ADR-0008.
- Una vez estable, se deprecará la rama REST interna en favor de MCP.
