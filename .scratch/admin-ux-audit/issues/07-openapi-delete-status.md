# Issue 07 — Alinear openapi.yml DELETE users con backend

- **Status:** completed
- **Verified:** 2026-10-04 — `openapi.yml` documenta 200 + schema real para DELETE users; gate `canonical-openapi.py` verde.
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
- [x] `openapi.yml` describe 200 para DELETE users.

## Comments
- 2026-10-04 (agente): regresión detectada en commit `555f906` (`'200'→'204'`). Corregido explicitando `status=status.HTTP_200_OK` en `admin_views.py:272` y schema `200` con body en `openapi.yml:269`. Gate verde.
