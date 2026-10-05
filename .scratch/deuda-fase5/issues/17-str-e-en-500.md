# Issue 17: str(e) fuera de respuestas + permisos schema/mock

Status: ready-for-human
Sev: P1 · Área: backend · Fase: D

## Evidencia
- `str(e)` a Response 500/502/503 en `training_data/views.py:107-111,174-177,253-256`,
  `ai_models/views.py:84-85,111-112,145-147,168-169`, `authentication/views.py`
  (múltiples `except Exception` + tasks `:75-76,129-130` sin retry).
- `settings.py:422` `SPECTACULAR SERVE_PERMISSIONS AllowAny`;
  `core/api_views.py:41-44` `mock_sensor_data AllowAny` legacy.

## Problema
Fuga de detalle interno; superficie abierta sin dueño.

## Aceptación
- [x] Errores tipados con códigos (sin `str(exc)` al cliente; log estructurado interno).
- [ ] Retry con backoff en tasks de correo → continúa en `08-retry-backoff.md`.
- [x] Schema con auth (`SPECTACULAR_SETTINGS.SERVE_PERMISSIONS=IsAuthenticated`).
- [x] `mock_sensor_data` restringido a staff y retornado `410 Gone`.
- [x] Ruff + tests de los endpoints tocados en verde.

## Compliance
LFPDPPP: no exponer trazas/detalles; mínimo privilegio.

## Comments
- 2026-10-04 (agente): corregidos 9 `str(e)` en `training_data/views.py`, `ai_models/views.py`, `authentication/views.py`; `mock_sensor_data` pasa a staff+410; schema bajo auth. Tests verdes. Retry de correo queda fuera (issue 08).
