# 02-vision-safety-gate

Status: ready-for-agent

## Título
Safety gate post-inferencia en `analyze_vision_async` (MS1)

## Descripción
Después de recibir la respuesta de MS1 en el worker Celery (`apps/ai_models/tasks.py:55`), escanear el JSON completo con `SafetyValidator`. En caso de violación:
- No crear `AIDiagnostic`.
- Registrar `AuditLog` con `action='SAFETY_BLOCK_<CODE>'`, `source='vision'`, `details` JSON (task_id, code, reason, species detectada).
- Retornar payload con `{"blocked": true, "safety_block": {"code": ..., "reason": ...}}` para que el polling lo sirva.

## Tareas
1. Importar `SafetyValidator` en `apps/ai_models/tasks.py`.
2. Después de `result = response.json()`, ejecutar validación sobre texto completo.
3. En violación: crear `AuditLog`, omitir `AIDiagnostic.objects.create`, retornar payload bloqueado.
4. Tests en `apps/ai_models/tests/test_vision_safety_gate.py`:
   - Mock MS1 con respuesta "peyote" → resultado blocked + 1 AuditLog + 0 AIDiagnostic.
   - Mock MS1 con respuesta "tomate" → AIDiagnostic creado + 0 AuditLog.
   - Mock MS1 con acciones inmediatas que mencionen especie protegida → blocked.

## Criterios de aceptación
- Suite backend completa verde, cobertura ≥ 80%.
- `ruff check` limpio en archivos tocados.
