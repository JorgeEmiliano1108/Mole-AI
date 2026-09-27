# PRD — Hito 4: Trazabilidad y Cierre de Seguridad

## Objetivo
Cerrar las brechas periféricas del `SafetyValidator` determinístico para cumplir con estándares internacionales (ISO 27001, IEEE 7000) y garantizar trazabilidad regulatoria inmutable de bloqueos de seguridad.

## Alcance
1. Hacer `AuditLog` verdaderamente append-only (ORM + trigger PostgreSQL).
2. Interceptar la salida del microservicio de visión (MS1) en el worker Celery del monolito, aplicar `SafetyValidator` post-inferencia y persistir el bloqueo en `AuditLog`.
3. Extender el contrato de polling de visión con el campo `safety_block` para que Flutter renderice el banner rojo existente.
4. Poblar datos reales de agroquímicos/especies queda **fuera de alcance** (curación manual por experto agrónomo posterior).

## Decisiones arquitectónicas aprobadas
- Reutilizar el modelo `AuditLog` existente con `action='SAFETY_BLOCK_<CODE>'`.
- Implementar trigger PostgreSQL `BEFORE UPDATE OR DELETE` sobre `audit_logs`.
- Escanear el texto completo del JSON de respuesta de MS1 (fail-closed).

## Regulaciones aplicables
- **LGEEPA / NOM-059-SEMARNAT**: protección de especies endémicas; avisos obligatorios en UI.
- **ISO/IEC 25001**: trazabilidad y calidad de requisitos.
- **ISO 27001**: inmutabilidad de registros de auditoría.
- **LFPDPPP**: en `AuditLog.details` no se almacenará PII, solo IDs, códigos y clases detectadas.

## Criterios de aceptación
- Cobertura backend ≥ 80% y linter sin warnings en archivos tocados.
- Tests de `AuditLog` demuestran que `update()`, `delete()` y bulk delete lanzan excepción.
- Tests de visión demuestran que un resultado MS1 con "peyote" genera `safety_block` + `AuditLog`, sin crear `AIDiagnostic`.
- Flutter tests verdes y `SafetyBlockBanner` visible ante bloqueo de visión.
