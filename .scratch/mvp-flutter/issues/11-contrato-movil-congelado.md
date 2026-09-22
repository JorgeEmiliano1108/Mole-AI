# 11 — Contrato móvil congelado (snapshot OpenAPI + cliente Dart)

Status: ready-for-human

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

Congelar el contrato que consumirá el APK: snapshot versionado del schema OpenAPI (`docs/contracts/openapi.yml`), lista explícita de endpoints móviles (in/out), cliente Dart manual contra el contrato (`mobile/lib`, tipado por dominio), y gate CI `schema-diff` que falla si el schema cambia sin actualizar el contrato.

Vías congeladas (decisión usuario 2026-09-17): visión **async vía Django+Celery** (`POST diagnostics/` → poll `ai/vision/status/`); chat **vía gateway** (`POST llm/chat/`); 7 historias + offline real.

## Acceptance criteria

- [x] `docs/contracts/openapi.yml` generado desde `drf-spectacular` (`/api/schema/`) y versionado
- [x] `docs/mobile-contract.md` lista endpoints móviles con `path:línea` de la vista que los sirve; stubs/mock excluidos explícitamente
- [x] Gate CI `schema-diff`: regenera schema y falla con diff no vacío
- [x] Cliente Dart manual contra el contrato (`mobile/lib`, `flutter analyze` 0 issues)
  — NOTA: se descartó `openapi-generator` (el schema de vistas-función es estructural;
  el cliente manual tipado por dominio + tests por endpoint da más rigor con menos
  fricción; decisión reversible si el schema se enriquece con `@extend_schema`).

## Blocked by

- `01-gobernanza-harness.md`
- `02-auth-hs256.md`

## Comments

- 2026-09-17 (agente): skill `to-issues`. Excluidos del contrato: `batch` (solo `edge-batch`), `POST sensors/ingest` (M2M), stubs (`sensor-logs/`, `plant-knowledge/`, `fichas/`, `history/`), mock `GET sensor-data/latest/` (dev).
- 2026-09-17 (agente): **cambio declarado Fase 1** — `DEFAULT_PAGINATION_CLASS=PageNumberPagination/PAGE_SIZE=50` (`settings.py`): `GET plants/species/` pasa a envelope `{count,next,previous,results}` (única vista afectada; web ya tolerante en `main.js:46`). `GET health/` pasa a `AllowAny` explícito (ping pre-login). Reorden `favorites/` antes de `<uuid>/` (`urls_user.py`, sin cambio de comportamiento). Snapshot `openapi.yml` regenerado; gate `schema-diff` verde.
- 2026-09-17 (agente): **cambio declarado Fase D** — MS3 monta `prefix="/api/v1/reports"` (`mole_report/app/main.py:41`): ambos nginx y el proxy Django (`admin_views.py:124-146`) ya llamaban con prefijo (404 antes). Tests MS3 alineados (`P="/api/v1/reports"`). APK usa rutas exactas sin `/` (`enforceSlash:false`). Django schema intacto (gate verde sin regenerar).
- 2026-09-18 (agente): **cambios declarados B2/B3** — `register_view` exige `consent:true`
  (400 LFPDPPP); `login/refresh` emiten `jti`; `logout_view` revoca vía denylist
  (Redis/locmem, TTL=vida restante). Solo cambia descripción del schema (docstring
  logout); paths/métodos idénticos. Snapshot regenerado; gate verde.
- 2026-09-19 (agente): **cambio declarado F3** — nuevo `POST /api/v1/sync/batch/`
  (JSON-RPC 2.0 `sync.telemetry` con cursor; dual-stack, `edge-batch/` intacto).
  Snapshot `openapi.yml` regenerado (77→78 paths); gate verde.
