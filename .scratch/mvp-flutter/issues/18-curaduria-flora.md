# 18 — Curaduría flora endémica (bloquea portal)

Status: ready-for-human

> Asignado a humano (Fase 2, veredicto arquitectónico 2026-09-22): la curaduría
> de fichas y la firma de revisión exigen juicio botánico. El merge requiere
> revisión firmada en este issue antes de que el portal consuma las fichas.

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

Fichas verificadas de flora endémica mexicana con fuente citada por ficha (científico/común, hábitat, distribución, usos, imagen con licencia, `is_protected_nom059` + `protection_warning` donde aplique). Ninguna ficha sin fuente entra al seed. Requiere revisión humana del lote antes de merge.

## Acceptance criteria

- [ ] Seeds ampliados con `is_endemic=true` + fuentes
- [ ] Revisión humana firmada en este issue
- [ ] Portal público solo consume fichas curadas

## Blocked by

- `16-password-reset.md` (campo `is_endemic` + backfill)
