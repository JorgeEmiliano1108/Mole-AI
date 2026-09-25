# Issue 17: str(e) fuera de respuestas + permisos schema/mock

Status: ready-for-agent
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
- Errores tipados con códigos (sin `str(exc)` al cliente; log estructurado interno);
  retry con backoff en tasks de correo.
- Schema con auth y `mock_sensor_data` eliminado o tras permiso staff.
- Ruff + tests de los endpoints tocados en verde.

## Compliance
LFPDPPP: no exponer trazas/detalles; mínimo privilegio.

## Comments
(none)
