# 17 — BLE live telemetry (firmware + app)

Status: ready-for-agent

## Parent

`.scratch/mvp-flutter/PRD.md`

## What to build

ADR-0005. **Firmware** (ESP-IDF, C): characteristic `FEE2` `READ+NOTIFY` (+CCC) con telemetría; GATT vivo fuera de `FSM_PROVISIONING`; coexistencia WiFi+BLE + deep-sleep (ventanas/modo campo-cercano documentado); `SECURITY_1`; MTU/chunking; tests HW. **App**: `flutter_blue_plus` + `permission_handler`; manifest `BLUETOOTH_SCAN/CONNECT` (+`ACCESS_FINE_LOCATION` <API31); provisioning `FEE1` (write JSON) + subscribe `FEE2` + badge origen (BLE-live vs servidor) + merge con `telemetry/latest/`. Sin BLE todo sigue vía backend (fallback permanente).

## Acceptance criteria

- [ ] Spec GATT documentada antes del firmware
- [ ] Tests HW en verde + prueba campo (batería medida)
- [ ] App subscribe/desubscribe testeado con fake adapter BLE
- [ ] `flutter analyze` 0 issues

## Blocked by

- `14-portal-publico.md` (Mis plantas es la superficie que muestra BLE)

## Diferido a V2.0 — Acta F4 (2026-10-06, skills `triage` + `grill-with-docs`)
- Gemelo de `deuda-20-mobile-ble-stack` (misma acta): stack BLE real
  diferido a post-MVP por decisión de usuario (telemetría solo-servidor).
- Lo hecho queda: badge origen + merge con `telemetry/latest/`
  (`plants.dart:233`, testeado); provisioning FEE1 + subscribe FEE2 +
  tests HW/campo quedan para V2 (criterios 1-3 sin marcar).
- Bloqueo por 14 resuelto (portal existe); el bloqueo vigente es
  hardware + prueba campo, no código. Status queda `ready-for-agent`.
