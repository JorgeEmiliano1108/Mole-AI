# 03-chat-async-safety-gate

Status: ready-for-agent

## Título
Safety gate en `chat_async` (chat RAG fallback asíncrono)

## Descripción
Validar la respuesta del LLM dentro del worker Celery `chat_async` (`apps/core/tasks.py:87`) antes de retornar el payload. En bloqueo, retornar `{blocked: true, safety_block: {code, reason}}` y registrar `AuditLog` con `source='chat_fallback'`.

## Tareas
1. En `chat_async`, tras obtener `result`, extraer `respuesta` y validar con `SafetyValidator`.
2. En violación: `log_safety_block(..., source='chat_fallback')`, no crear `LLMRequest`, retornar payload bloqueado.
3. Tests: `apps/core/tests/test_chat_async_safety_gate.py` con `MoleAIClient` mockeado.

## Criterios de aceptación
- Tests verdes; suite completa ≥ 80%.
- `ruff check` limpio.
