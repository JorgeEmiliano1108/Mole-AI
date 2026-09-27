# 01-auditlog-append-only

Status: ready-for-agent

## Título
Hardening AuditLog: append-only a nivel ORM y trigger PostgreSQL

## Descripción
El modelo `AuditLog` (`apps/core/models.py:204`) ya protege `save()` y `delete()` a nivel de instancia, pero `QuerySet.update()`, `QuerySet.delete()` y bulk operations lo bypassan. Este issue cierra esa brecha.

## Tareas
1. Crear `AuditLogQuerySet` con `update()`, `delete()` y `bulk_update()` que lancen `PermissionError`.
2. Asignar `objects = AuditLogQuerySet.as_manager()` en `AuditLog`.
3. Crear migración `0016_auditlog_immutable_trigger` con `RunSQL` que instale trigger `BEFORE UPDATE OR DELETE ON audit_logs` en PostgreSQL.
4. Escribir `apps/core/tests/test_auditlog_append_only.py` con TDD:
   - Inserción permitida.
   - `instance.delete()` lanza.
   - `instance.save()` con pk lanza.
   - `AuditLog.objects.update()` lanza.
   - `AuditLog.objects.delete()` lanza.
   - Trigger DB: intentar UPDATE/DELETE raw SQL lanza excepción.

## Criterios de aceptación
- `pytest apps/core/tests/test_auditlog_append_only.py` verde.
- Cobertura global ≥ 80%.
- `ruff check` limpio en archivos tocados.
