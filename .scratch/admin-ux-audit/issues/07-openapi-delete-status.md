# Issue 07 — Alinear openapi.yml DELETE users con backend

- **Status:** ready-for-human
- **Verified:** 2026-09-30 — `openapi.yml` documenta 200 + schema real para DELETE users.
- **Priority:** low
- **Skill:** grill-with-docs

## Problema
`openapi.yml` documenta `DELETE /admin/users/{user_id}/` como respuesta 204, pero el backend responde 200 con cuerpo `{"status":"deactivated"}`.

## Evidencia
- `docs/contracts/openapi.yml:219-270`
- `core_backend/apps/core/admin_views.py:272`

## Solución
Actualizar `openapi.yml` para reflejar 200 + schema real. No se cambia backend para no romper el contrato ya consumido.

## Tests
- Ninguno; revisión manual del contrato.

## Criterio de aceptación
- `openapi.yml` describe 200 para DELETE users.
