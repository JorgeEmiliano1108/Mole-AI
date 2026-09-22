# 12 — Coherencia código ↔ docs (CONTEXT, README, audit-matrix)

Status: ready-for-agent

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

Sincronizar la documentación con el código verificado: deuda canónica stale en `CONTEXT.md`, claims de README, y nueva versión de `audit-matrix.md` tras congelar el contrato móvil.

Hallazgos ya verificados (2026-09-17): `Sin-rotación` resuelto (migraciones `0012`/`0013` + `POST devices/<id>/rotate/`); `Consentimiento-solo-frontend` resuelto (`POST auth/consent/` + `AuditLog` + `frontend/privacy.html`); `tflite_adapter.py` inexistente (TD-02 resuelto); CI existe (`system-tests.yml`: `docs-consistency`, `license-check`, `system-tests`) — falta solo CD; resiliencia parcial (MQTT + Celery con tests; faltan Redis-down/PG-down).

## Acceptance criteria

- [ ] `CONTEXT.md` §deuda canónica refleja el estado real (resueltos marcados, pendientes con owner)
- [ ] `audit-matrix.md` v2.1: 20 claims ❌ re-adjudicados (doc-lie vs code-lie) o con plan fechado
- [ ] Gate `check-docs-consistency.sh` sigue verde tras los cambios

## Blocked by

- `11-contrato-movil-congelado.md`

## Comments

- 2026-09-17 (agente): skill `to-issues`. Regla operativa: ningún cambio de contrato sin actualizar docs en la misma pasada; toda afirmación con `path:línea`.
- 2026-09-17 (agente): deuda lint pre-existente registrada (no introducida en este plan): `core_backend/apps/core/views.py` tiene ~30 avisos ruff (F401 imports sin uso, UP006/UP035 `typing.Dict/List`, BLE001, RUF012 en atributos DRF — estos últimos son **falsos positivos**: DRF exige class attributes —, DTZ006). Limpieza completa diferida: requiere revisión línea por línea fuera del MVP. Criterio AGENTS.md se cumple en líneas tocadas.
