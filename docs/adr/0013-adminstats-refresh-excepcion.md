# ADR-0013: Excepción documentada a RNF-BE-01 — `REFRESH MATERIALIZED VIEW`

- **Fecha:** 2026-10-06
- **Estado:** Aceptado (Wave D)
- **Contexto:** RNF-BE-01 exige ORM sin SQL directo. Las vistas productivas ya usan ORM, incluido el acceso a la vista materializada `admin_stats` vía modelo no gestionado `AdminStats.objects.first()` (`core_backend/apps/core/admin_views.py:42-43`, `apps/core/models.py:352-365`, `managed=False`). Pero PostgreSQL no permite refrescar una MV vía ORM: el único mecanismo es `REFRESH MATERIALIZED VIEW CONCURRENTLY admin_stats` (`apps/core/tasks.py:80`).
- **Decisión:** se autoriza una única sentencia SQL fija, sin interpolación de entrada de usuario, ejecutada en worker Celery (`refresh_admin_stats_task`). Queda prohibido añadir `cursor.execute` con parámetros de request; cualquier SQL nuevo con entrada externa debe pasar por ORM o por revisión de seguridad explícita.
- **Consecuencias:** RNF-BE-01 → ✅ con esta excepción. Si la MV no existe (entorno sin migraciones aplicadas), el refresh falla en el worker sin afectar requests (tarea aislada, reintentable por Celery).
- **Cumplimiento:** `enforce-compliance` (excepción documentada, no silencio); sin PII (solo agregados).
