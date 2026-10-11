# 04 — Telemetría trama edge + lectura móvil

Status: needs-triage

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

Ingesta canónica `edge-batch` (ADR-0002): 1 serializer, anti-replay 300s único, `bulk_create`, `HardwareOnlyPermission` en `EdgeNodeIngestView` (hoy `AllowAny`), `batch` como alias deprecado; `store_forward_daemon.BACKEND_BATCH_URL` a `edge-batch`; `HealthRepository` pura (derivación `online/warning/offline`) + `OfflineQueue` web; nodos dormidos tolerados.

## Acceptance criteria

- [ ] `pytest` m2m/batch/edge + ownership/revocación en verde
- [ ] mapeo telemetría/health en APK en verde (`mobile/test/plants_vision_test.dart`; pivot V2, sin vitest)
- [ ] E2E `ESP32→Django→lectura` con SQLite Store&Forward 30s/batch 200
- [ ] TLS Fail-Safe verificado (sin texto plano)

## Blocked by

- `01-gobernanza-harness.md`
- `02-auth-hs256.md`

## Diferido parcial a V2.0 — Acta F4 (2026-10-06, skills `triage` + `grill-with-docs`)
- HECHO (veredicto forense, sin código nuevo): ingesta canónica
  `edge-batch` con `DeviceBearer` real + throttle, `ingest_frame` con
  `bulk_create` + dedupe idempotente, `telemetry/latest/` + health con
  BOLA, lectura APK testeada (`plants_vision_test.dart`, badge F1).
- DIFERIDO V2.0: alias `batch` deprecado, alineación de contrato del
  daemon (`sync_to_backend` emite `{"batch"}` incompatible — ROTO
  documentado, no silencioso), E2E ESP32→Django con hardware, TLS
  Fail-Safe verificado (depende de P0-03, también diferido).
- Status queda `needs-triage` hasta que V2 retome la parte daemon/HW.
