# 01-safety-audit-module

Status: ready-for-agent

## Título
Crear módulo centralizado `apps/core/services/safety_audit.py` y refactorizar visión

## Descripción
Actualmente `_log_safety_block` vive en `apps/ai_models/tasks.py`. Extraerlo a un servicio reutilizable para que `llm_chat_view` y `chat_async` lo consuman sin duplicar lógica de auditoría.

## Tareas
1. Crear `apps/core/services/safety_audit.py` con `log_safety_block(user_id, safety_result, task_id, source)`.
2. Refactorizar `apps/ai_models/tasks.py` para importar y delegar en `safety_audit.log_safety_block`.
3. Asegurar que `test_vision_safety_gate.py` sigue pasando tras el refactor.

## Criterios de aceptación
- `pytest apps/ai_models/tests/test_vision_safety_gate.py` verde.
- `ruff check` limpio en archivos tocados.
