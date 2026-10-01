# Issue 03 — Restringir listados de training a admin

- **Status:** ready-for-human
- **Verified:** 2026-09-30 — `IsAdminUser` en listados training; usuario normal 403, admin 200; tests pasan.
- **Priority:** high
- **Skill:** enforce-compliance + tdd

## Problema
`GET training/documents/` e `GET training/images/` usan solo `IsAuthenticated`. Cualquier usuario autenticado puede listar el dataset de entrenamiento (datos internos de MLOps).

## Evidencia
- `core_backend/apps/training_data/views.py:265,277`
- `core_backend/apps/training_data/urls.py:31-40`

## Solución
Añadir `IsAdminUser` a ambas vistas.

## Tests
- Backend: usuario normal → 403; admin → 200.

## Criterio de aceptación
- `flutter test` sigue pasando (la app consume con admin).
- `pytest` pasa con nuevo test de permisos.
