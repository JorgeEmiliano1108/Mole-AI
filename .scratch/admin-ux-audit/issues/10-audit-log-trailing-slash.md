# Issue 10 — Trailing slash en GET admin/audit-log

- **Status:** ready-for-human
- **Verified:** 2026-09-30 — Se normalizaron a `/` final todas las rutas admin en `admin.dart` (`statistics/`, `live-alerts/`, `system-events/`, `audit-log/`, `devices/`, `users/`); test de contrato pasa; `flutter analyze` limpio.
- **Category:** bug
- **Priority:** low
- **Skill:** tdd + grill-with-docs

## Problema
`core_backend/apps/core/admin_views.py` o `apps/core/views.py` expone `GET /api/v1/admin/audit-log/` (con `/` final, corregido en Issue 01), pero `mobile/lib/features/admin/admin.dart:236` llama `_api.getJson('admin/audit-log', query: ...)` **sin `/` final**. Hoy funciona porque Django `APPEND_SLASH=True` devuelve 301 y el cliente lo sigue, pero viola el contrato §0 que establece trailing slash obligatorio.

## Evidencia
- `mobile/lib/features/admin/admin.dart:236`: `await _api.getJson('admin/audit-log', query: {...})`.
- `core_backend/apps/core/urls.py`: ruta registrada como `admin/audit-log/`.

## Solución
- Cambiar la llamada a `admin/audit-log/`.
- Agregar test de contrato (unitario) que verifique que las rutas admin consumidas por la app usen `/` final.

## Tests
- Test en `mobile/test/admin_portal_test.dart` o test específico de `AdminRepository`.

## Criterio de aceptación
- `flutter analyze` limpio.
- `flutter test` verde.
- La llamada a audit-log no genera 301 en logs del backend.
