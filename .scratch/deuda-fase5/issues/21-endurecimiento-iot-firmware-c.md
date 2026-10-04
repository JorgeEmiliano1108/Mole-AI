# Issue 21: Endurecimiento IoT (firmware C) — etapa dedicada, fuera del MVP

Status: needs-info
Sev: P2 · Área: firmware · Fase: endurecimiento-IoT

## Contexto
Decisión ejecutiva 2026-10-04: la migración del firmware ESP32 a Rust queda
**rechazada** (scope creep; todo el esfuerzo en P0/P1 del MVP). El firmware
productivo sigue en C sobre ESP-IDF 5.2.1 (`microservices/esp32_node/`,
~3.6k LOC, build CMake manual, sin job de firmware en CI). Esta issue
consolida la deuda C conocida para una etapa de endurecimiento IoT posterior.

## Deuda inventariada (no migrar, endurecer)
- **Chunking FEE2 vs MTU-23**: ver issue 10 (P1, `needs-info`) — `ble_fee2_publish`
  sin chequeo MTU ni `[seq][total]`; trama máx 31 B > útil ~20 B.
- **Seguridad BLE**: RNF-01 `SECURITY_0` (spec pedía 1); bonding en namespace
  `mole_prov` sin verificación adicional.
- **Flash encryption off** + identity removida pero zeroize aún con `memset`
  (BUG-02/04/05 en `microservices/esp32_node/docs/requisitos.md`).
- **Anti-replay**: RNF-05 sin nonce/contador en trama edge (solo Δt servidor).
- **I2C sin retry** (RNF-15); URIs por Kconfig requieren recompilar (TD-09).
- **CI**: sin job `idf.py build` ni tests host en pipeline (issue 12).

## Criterio de entrada a la etapa
P0/P1 del MVP cerrados + H6 verificado. Ningún cambio de lenguaje; solo
endurecimiento del C existente con sus 37 tests host como red de seguridad.
