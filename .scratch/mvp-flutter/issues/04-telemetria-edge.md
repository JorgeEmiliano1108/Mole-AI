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
