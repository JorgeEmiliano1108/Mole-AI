# 01 — Gobernanza y harness de tests

Status: ready-for-agent

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

Dejar el repo con tracker, glosario, ADRs y harness pytest ejecutable: `AGENTS.md`, `CONTEXT.md`, `docs/adr/0002+0003`, `core_backend/pytest.ini`, import defensivo `microservices.mole_report` en `apps/core/models.py:368` (origen del `ModuleNotFoundError` que excluye a Django de `docker-compose.e2e.yml`), y tests `middleware_order/prometheus` alineados a la realidad (sin `django-prometheus` instalado).

## Acceptance criteria

- [ ] `AGENTS.md`, `CONTEXT.md`, `docs/adr/0002-edge-batch-canonico.md`, `0003-hs256-local-mvp.md` existen
- [ ] `core_backend/pytest.ini` con `DJANGO_SETTINGS_MODULE=mole_ai_backend.settings` y marcadores `unit/integration/e2e`
- [ ] `apps/core/models.py` importa sin `microservices` montado (signal con `try/except`, reminder no-op con warning)
- [ ] `test_middleware_order` y `test_prometheus_metrics_endpoint` en verde contra el stack real (sin añadir dependencias)
- [ ] `pytest --collect-only` sin errores de importación en `apps/core/tests/`

## Blocked by

None - can start immediately

## Comments

- 2026-09-07 (agente): implementado estático. `py_compile` OK en los 3 `.py` tocados.
- Pendiente CI: `pytest --collect-only`, `pytest apps/core/tests/test_middleware_order.py`, `pytest apps/core/tests/test_prometheus_metrics_endpoint.py` (pivot V2: sin vitest; web retirada, E2E en pytest + `integration_test` Dart).
- Skills usadas: `setup-matt-pocock-skills` (tracker local confirmado, `AGENTS.md` creado — decisión reversible a `CLAUDE.md`), `grill-with-docs` (`CONTEXT.md` + ADR-0002/0003), `to-issues` (slices 01-08), `enforce-compliance` Fase 1/2/4 (sin TLS/uploads tocados en este slice; `safe_join` no aplica).
- Riesgo abierto: `tests/test_otel_trace_id_propagation.py` importa `app.infrastructure...` (paquete MS, no Django) — excluido en `pytest.ini` hasta moverlo a `mole_vision/tests/` (propuesto Slice 8).
- 2026-09-21 (pivot V2 web→Python/Dart, RNF03): frontend web retirado del ecosistema
  (admin = Django Admin RBAC, migración 0014 grupo Botánico); `frontend/scripts/check-docs-consistency.sh`
  retirado con él y el job CI `docs-consistency` eliminado. E2E: pytest servidor +
  `integration_test` Flutter; cero Node en el repo.
