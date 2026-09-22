# ADR-0005: Telemetría BLE en vivo (FEE2) con coexistencia deep-sleep

- **Fecha:** 2026-09-21
- **Estado:** Aceptado
- **Contexto:** El firmware solo expone provisioning BLE (`0xFEE0/0xFEE1`, WRITE único, `ble_provisioning.c:36-67`); tras provisioning el BLE muere y el nodo duerme 5 min (`state_machine.c:82-97`, `mole_config.h:64`). La app requiere plantas monitoreadas por ESP32 vía Bluetooth al celular.
- **Decisión:** Añadir servicio `FEE2` (o characteristic adicional) con `READ+NOTIFY` (+descriptor CCC) publicando telemetría JSON/CBOR; GATT vivo fuera de `FSM_PROVISIONING`; coexistencia WiFi+BLE documentada; deep-sleep por ventanas de anuncio o modo campo-cercano (costo batería explícito); `SECURITY_1` mínimo; MTU/chunking documentados. El path servidor (`edge-batch` → HTTP) queda como fallback permanente: sin BLE, todo sigue funcionando.
- **Consecuencias:** Trabajo ESP-IDF en C + tests HW (`README.md:196` los exige); la app usa `flutter_blue_plus` + permisos `BLUETOOTH_SCAN/CONNECT`; badge de origen en UI (BLE-live vs servidor).
- **Cumplimiento:** `enforce-compliance` IFT-016 (radio BLE) + `grill-with-docs` (spec GATT antes de codificar firmware).
