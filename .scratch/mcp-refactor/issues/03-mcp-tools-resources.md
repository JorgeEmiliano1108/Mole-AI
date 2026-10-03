# 03: A3: Implementar tools y resources MCP iniciales

Status: ready-for-agent

## Requisito

Definir las primeras tools y resources que exponen contexto dinámico al LLM.

## Acceptance criteria

- [ ] Tool `latest_readings(plant_id, hours_back=24)` reutilizando `SensorDataAggregator` vía puerto/adaptador.
- [ ] Tool `get_diagnosis_context(plant_id, limit=5)` leyendo `AIDiagnostic` filtrados.
- [ ] Resource `session://{user_id}/history` leyendo de `redis_session_store.py` / `LLMRequest`.
- [ ] Cada tool devuelve JSON serializable y maneja errores sin exponer PII.
- [ ] Tests de cada tool/resource con datos de prueba.

## Blocked by

- `02-mcp-server-scaffold`.

## Notas

Mantener bajo acoplamiento: las tools llaman a los mismos casos de uso que ya usa REST.

## Comments

**2026-10-02 — opencode**
Scaffold de tools implementado parcialmente:
- Tool `ping` (health-check).
- Tool `get_sensor_context(user_id)` que consume el `RedisSensorCacheAdapter` existente, inyectado desde el lifespan de FastAPI.
- Tests unitarios en `tests/test_mcp_server.py` (6 passed).

Pendiente: `latest_readings` granular por `plant_id`, `get_diagnosis_context` y resource `session://{user_id}/history` (requieren acceso a datos de Django o ampliar el contexto de Redis).

