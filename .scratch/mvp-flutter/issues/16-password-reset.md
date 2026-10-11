# 16 — Backend portal: password-reset + usuarios admin + flora endémica

Status: ready-for-human

## Resolución F4 (2026-10-06, skills `triage` + `grill-with-docs`)
- `ready-for-agent` → `ready-for-human` (código completo, verificado Wave 1):
  `password-reset/request|confirm` (TTL 1h, un solo uso, hash+pepper,
  anti-enumeración) + `password-change` + `AuditLog`;
  degradación honesta 501 sin SMTP (`PASSWORD_RESET_EMAIL_ENABLED`,
  ADR-0006 enmienda Wave D); admin users list/search/patch/soft-DELETE;
  `is_endemic` + `?endemic=&habitat=` + `live-alerts` en
  Ambient/SoilReading.
- Evidencia: `test_issue16_portal.py` (request/confirm/change/admin/flora,
  11 tests) + `mobile-contract.md` §1 (fila 501/202) + gate `schema-diff`.
  Criterios originales cubiertos (el "202" de anti-enumeración rige solo
  con SMTP habilitado, documentado).
- Resta humano: validación del revisor, no código.

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
