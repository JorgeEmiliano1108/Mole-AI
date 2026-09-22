# 05 — Visión diagnóstica

Status: needs-triage

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

`diagnostic_view` único → `analyze_vision_async timeout=30` contra `/api/v1/vision/analyze/` (slash); validación `10MiB + EXIF + magic-bytes` única con `safe_join`; retirar `consultar_phi_vision` HF duplicado; `VisionRepository(FormData→Multipart)` portable a `image_picker`.

## Acceptance criteria

- [ ] `pytest` vision status + rechazo `MZ/ELF` en verde
- [ ] submit+poll+reintento en APK en verde (`plants_vision_test.dart`; pivot V2, sin vitest)
- [ ] E2E `foto → {species,severity,ph_predicted,confidence}` en verde
- [ ] Cero `TypeError` por firma incompleta hacia PGVector/CNN

## Blocked by

- `01-gobernanza-harness.md`
- `02-auth-hs256.md`
