# 16 — Backend portal: password-reset + usuarios admin + flora endémica

Status: ready-for-agent

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

ADR-0006: `POST auth/password-reset/request|confirm` + `POST auth/password-change` (throttle, TTL 1h, un solo uso, `AuditLog`, reutiliza `validate_password_strength`). Admin usuarios: `GET admin/users/?search=&role=` + `PATCH admin/users/<id>` + `DELETE` (respeto ARCO). Flora: migración `is_endemic:bool` + índice en `SpeciesCatalog` + backfill seeds; `search/` acepta `?endemic=&habitat=` y expone `habitat/uses/image_url`; migrar `live-alerts` a `Ambient/SoilReading`.

## Acceptance criteria

- [ ] Tests pytest por endpoint (401/403/400/409 + anti-enumeración 202)
- [ ] Gate `schema-diff` verde + `mobile-contract.md` actualizado
- [ ] `ruff` limpio en tocados

## Blocked by

None - can start immediately
