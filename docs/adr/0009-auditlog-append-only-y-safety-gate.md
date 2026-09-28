# ADR-0009: AuditLog inmutable y safety gate post-inferencia para MS1

- **Fecha:** 2026-09-27
- **Estado:** Aceptado
- **Contexto:** Hito 4 — Trazabilidad y Cierre de Seguridad. El `SafetyValidator` determinístico (Hito 3) protegía diagnósticos por texto y agroquímicos, pero faltaba (1) cerrar el pipeline de visión MS1 y (2) dejar rastro inmutable de los bloqueos para auditorías regulatorias (ISO 27001, IEEE 7000, LGEEPA/NOM-059).

## Decisiones

### 1. Reutilizar `AuditLog` con protección append-only dual
- No se creó tabla nueva; se extendió el uso de `AuditLog` (`apps/core/models.py`) con `action='SAFETY_BLOCK_<CODE>'` y `details` JSON.
- Se añadió `AuditLogQuerySet` para prohibir `update()`, `delete()` y `bulk_update()` a nivel ORM.
- Se añadió migración `0016_auditlog_immutable_trigger` con un trigger PostgreSQL `BEFORE UPDATE OR DELETE` que lanza excepción. Esto garantiza inmutabilidad a nivel de motor, no solo de ORM.

### 2. Safety gate en el worker Celery, no en MS1
- El punto de corte es `analyze_vision_async` (`apps/ai_models/tasks.py`), después de recibir el JSON de MS1 y antes de crear `AIDiagnostic`.
- Se escanea el texto completo de la respuesta con `SafetyValidator` (fail-closed).
- En violación: se escribe `AuditLog`, no se persiste el diagnóstico, y se retorna `{blocked: true, safety_block: {code, reason}}`.
- MS1 no se acopla al monolito; sigue siendo un servicio HTTP puro. La latencia es nula para el usuario porque la validación ocurre dentro del worker asíncrono.

### 3. Contrato de polling extendido
- `GET /api/v1/ai/vision/status/<task_id>/` ahora puede devolver `result.blocked` y `result.safety_block`.
- Flutter (`VisionStatus`) parsea estos campos y renderiza `SafetyBlockBanner` en `DiagnosisScreen`.

## Consecuencias
- Los falsos positivos por escaneo de texto completo son tolerados frente a evasión por campos anidados inesperados (fail-closed).
- El trigger PostgreSQL impide que administradores con acceso a la base de datos modifiquen o borren registros de auditoría.
- La población real de `docs/safety/*.json` queda fuera de este ADR; será curada manualmente por un experto agrónomo.

## Cumplimiento
- **ISO 27001 / IEEE 7000**: registros de auditoría inmutables y trazables.
- **LGEEPA / NOM-059**: doble capa de protección (MS1 + monolito) con aviso obligatorio en UI.
- **LFPDPPP**: `AuditLog.details` no contiene PII; solo IDs, códigos de seguridad y clases detectadas.
