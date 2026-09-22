# 07 — Mapa, clima y reportes

Status: needs-triage

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

`MapRepository(hotspots→cluster, weather proxy)` online (offline fase 2); MS-3 único (`generate→status→download` presigned, `timeout 30`, forward `Authorization`, `hashed_user_id`); retirar PDF ReportLab local.

## Acceptance criteria

- [ ] `test_map_hotspots` 9 casos en verde
- [ ] E2E `report generate→download` en verde
- [ ] Spec `flutter_map + fl_chart + pdf/printing` documentada en `docs/mobile-contract.md`

## Blocked by

- `01-gobernanza-harness.md`
- `02-auth-hs256.md`
