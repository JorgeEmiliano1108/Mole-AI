# ADR-0002: Trama edge como contrato canónico de ingesta

- **Fecha:** 2026-09-07
- **Estado:** Aceptado
- **Contexto:** Dos contratos de ingesta coexisten: `POST sensor-data/batch/` (verbose, `X-Hardware-Api-Key`, `SensorBatchSerializer max 500`) y `POST sensor-data/edge-batch/` (compacto `EdgeFrame {ts,ri,a,s,dg}`, `Bearer Device.auth_token`). El firmware ESP32 (`microservices/esp32_node/main/transport_layer.c:138`, `edge_frame.h:46`, buffer 512B, `timeout 10000ms retry 3`) solo habla trama edge. `edge_node/store_forward_daemon.py:240` apunta a `batch`. El móvil Flutter solo lee (`telemetry/latest`, `devices/<id>/health`), no ingiere.
- **Decisión:** `sensor-data/edge-batch/` es el contrato canónico para hardware. `sensor-data/batch/` queda como alias deprecado 1 release (header `Deprecation: true` + log), luego 410. `store_forward_daemon.py:BACKEND_BATCH_URL` migra a `edge-batch`. Un solo serializer (`EdgeFrameSerializer`) + una ventana anti-replay (300s) + `bulk_create`.
- **Consecuencias:** Firmware sin cambios; `store_forward_daemon` + `mqtt_listener` se actualizan; Flutter no afectado (solo lectura). Riesgo: nodos con firmware viejo que usen `batch` → mitigado por alias temporal + test E2E `edge-batch` en `docker-compose.e2e.yml`.
- **Cumplimiento:** `enforce-compliance` Guardrail A (TLS + Fail-Safe SQLite Store&Forward, nunca texto plano).
