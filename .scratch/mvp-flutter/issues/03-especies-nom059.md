# 03 — Especies y NOM-059

Status: needs-triage

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

`SpeciesCatalog` + `plants/search/?q&category=` + `protection_warning` unificados; disclaimer `bg-red-500/10 border-red-500/30` obligatorio en web y spec Flutter; regex NOM-059 central único; `safeHTML` único.

## Acceptance criteria

- [ ] `test_nom059` (P/T/Pr) en verde
- [ ] búsqueda + widget NOM-059 en verde (`mobile/test/species_test.dart`; pivot V2, sin vitest)
- [ ] E2E `biznaga → 403 + disclaimer` en verde
- [ ] Sin overblock: especies no protegidas sin fricción

## Blocked by

- `01-gobernanza-harness.md`
