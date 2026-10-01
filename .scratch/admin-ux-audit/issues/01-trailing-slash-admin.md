# Issue 01 — Trailing slash en endpoints admin

- **Status:** ready-for-human
- **Verified:** 2026-09-30 — curl loop devuelve 200/401 en `admin/statistics/`, `admin/live-alerts/`, `admin/system-events/`, `admin/audit-log/`; tests backend pasan.
- **Priority:** high
- **Skill:** diagnose + tdd

## Problema
`ApiClient` fuerza `/` final por contrato, pero Django registró 4 rutas admin sin slash. La app recibe 404 en:
- `admin/statistics`
- `admin/live-alerts`
- `admin/system-events`
- `admin/audit-log`

También se normalizan al mismo tiempo `admin/report-text`, `admin/reports/generate`, `admin/reports/<job_id>/status` y `reports/users` para mantener consistencia.

## Evidencia
- `mobile/lib/features/admin/admin.dart:213,216,224,236`
- `core_backend/apps/core/urls.py:67,68,73,74,75,77,78,81`
- curl: `GET /api/v1/admin/statistics/` → 404; `GET /api/v1/admin/statistics` → 401.

## Solución
Agregar `/` final a las rutas admin en `core_backend/apps/core/urls.py`.

## Tests
- Backend: test que las rutas respondan 200/401 (no 404) con y sin auth.
- (Opcional) Flutter: no cambia código cliente; la validación es vía curl loop.

## Criterio de aceptación
- curl loop devuelve 401 (ruta existe) para `admin/statistics/`, `admin/live-alerts/`, `admin/system-events/`, `admin/audit-log/`.
