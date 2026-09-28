# 02-llm-chat-safety-gate

Status: ready-for-agent

## Título
Safety gate en `llm_chat_view` (chat RAG síncrono)

## Descripción
Interceptar la respuesta de MS2 en `apps/core/views.py:llm_chat_view` entre `response.json()` y `LLMRequest.objects.create`. Si el SafetyValidator bloquea, retornar 403 con `{error, code, source: 'chat'}` y persistir `AuditLog` vía `safety_audit.py`.

## Tareas
1. Importar `SafetyValidator` y `log_safety_block` en `apps/core/views.py`.
2. Después de obtener `ai_response`, ejecutar `SafetyValidator().validate({"text": ai_response})`.
3. En violación: `log_safety_block`, no crear `LLMRequest`, retornar 403.
4. TDD: `apps/core/tests/test_chat_safety_gate.py`:
   - Mock MS2 con respuesta "peyote" → 403 + `AuditLog` + 0 `LLMRequest`.
   - Mock MS2 con respuesta segura → 200 + `LLMRequest` + 0 `AuditLog`.
   - Mock MS2 con respuesta vacía o None → 200.

## Criterios de aceptación
- Suite backend completa verde, cobertura ≥ 80%.
- `ruff check` limpio.
