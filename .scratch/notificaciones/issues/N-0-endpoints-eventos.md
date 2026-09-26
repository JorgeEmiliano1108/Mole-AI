# Issue N-0: Endpoints my-alerts + system-events

Status: ready-for-human
Sev: P0 · Área: backend · Fase: N-0

## Problema
Sin superficie de eventos: botánico ciego a sus plantas, admin sin fallas sistema.

## Aceptación
- `GET /api/v1/user-plants/my-alerts/` (IsAuthenticated): umbrales live-alerts
  filtrados (`binding__plant__user`, `device__owner`) + liveness de dispositivos
  propios (warning/offline) + info estable si vacío. Cap 20.
- `GET /api/v1/admin/system-events` (IsAdminUser): secciones `security`
  (AuditLog PASSWORD_*/ADMIN_*/DELETE_ACCOUNT), `devices` (offline/warning global),
  `telemetry` (helper compartido con live-alerts), `services` (probe /metrics
  ms1:8001, ms2:8002, ms3:8003, timeout 2 s).
- Tests: owner ve propias / otro no; 401 anónimo; admin 200 + secciones;
  botánico 403 en system-events. OpenAPI actualizado.
- `pytest` nuevos en verde (vía docker, sin venv local).

## Compliance
RBAC estricto; sin PII en mensajes; NOM-059 fuera de alcance aquí.

## Comments
Resuelto: `alerting.py` compartido (live_alerts refactorizado sin cambio de
contrato, incl. fallback sensorlog con source original); `my-alerts/` scoped +
liveness propia; `system-events` con 4 secciones (AuditLog sin IP); RBAC 403
verificado; OpenAPI actualizado. Hallazgo al verificar: settings.py usaba
`_env_first` antes de definirlo (NameError en producción, el "import bug" que
excluía a django del e2e) — movida la definición arriba. Evidencia: 7 tests
nuevos + 71 (core/plants/auth) en verde vía docker.
