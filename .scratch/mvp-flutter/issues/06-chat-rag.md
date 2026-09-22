# 06 — Chat RAG única vía Celery

Status: needs-triage

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

`chat_fallback` (Celery `chat_queue`, timeout 120) como vía única; retirar `llm_chat_view` síncrono o tras flag; timeout/throttle únicos; `citation_manager + disclaimer` únicos; separar canal Redis `mole:training:pdf` vs `mole:training:image` (hoy ambos MS consumen `new_asset`).

## Acceptance criteria

- [ ] `pytest` usecase/breaker/PII en verde
- [ ] E2E `chat + disclaimer` en verde
- [ ] `pytest` API diagnostics→`llm/chat` con contexto+disclaimer (reemplaza spec Playwright, pivot V2)
- [ ] Idempotencia ante doble-consume verificada

## Blocked by

- `01-gobernanza-harness.md`
- `02-auth-hs256.md`
