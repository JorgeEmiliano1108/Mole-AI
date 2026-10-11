# 07 — Mapa, clima y reportes

Status: ready-for-human

## Triage F4 (2026-10-06, skill `triage`)
- `needs-triage` → `ready-for-human`. Desglose por criterio (decisiones de
  usuario registradas):
  - HECHO: `hotspots` + weather proxy (`map.dart`, testeado incl. skip de
    inválidos F1); MS-3 `generate→status→download` presigned
    (`reports.dart` + `ReportsScreen`, widget tests F1 éxito/Reintentar).
  - RECHAZADO: retirar ReportLab local (decisión: coexisten local/MS3
    documentados) y `fl_chart` (evitado explícito en `pubspec.yaml:55-56`;
    `charts.dart` usa CustomPainter).
  - DIFERIDO V2.0: clustering de hotspots (cosmético, mandato anti-refacto).
- Criterios originales re-mapeados: `test_map_hotspots` cubierto por
  `hotspots()` + `n3_test` + `f1_screens_test`; E2E report cubierto a nivel
  repo/UI con fakes (E2E con MS3 vivo = hold infra, ver N-4).

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
