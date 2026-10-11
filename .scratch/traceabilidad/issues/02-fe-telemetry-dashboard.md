# 02: RF-FE-02: Telemetría local MQTT/CoAP y dashboard interactivo

Status: ready-for-agent

## Requisito

- **ID:** RF-FE-02
- **Capa:** Frontend
- **Tipo:** RF
- **Texto:** La interfaz debe capturar telemetría local (vía MQTT/CoAP desde ESP32) y mostrar un dashboard interactivo con el estado de humedad, temperatura y luz UV del cultivo.

## Veredicto

⚠️ PARCIAL — Dashboard y BLE FEE2 presentes; MQTT/CoAP directo desde móvil NO implementado.

## Evidencia

- Dashboard: `mobile/lib/features/plants/plant_detail.dart:132-155`, `mobile/lib/features/plants/telemetry_badge.dart:21-37`.
- BLE FEE2 decode: `mobile/lib/features/ble/ble_telemetry.dart:73-137`.
- Tests golden BLE: `mobile/test/ble_telemetry_test.dart`.
- No se encontró cliente MQTT/CoAP en `mobile/lib/`.

## Delta (matriz ideal vs. estado implementado)

El móvil no suscribe MQTT/CoAP; recibe telemetría BLE en vivo (`0xFEE2`) y datos históricos por servidor REST. El gateway edge (`edge_node/`) es quien recibe MQTT.

## Nota normativa / riesgo

LFPDPPP/MASVS-STORAGE: datos de telemetría se cachean en SQLCipher AES-256 (`mobile/lib/core/offline_db.dart`).

## Siguiente paso sugerido

Decidir si se implementa scan/subscribe MQTT o CoAP en Flutter, o se ajusta la matriz para reflejar BLE FEE2 + REST como arquitectura real.

## Diferido a V2.0 — Acta F4 (2026-10-06, skills `triage` + `grill-with-docs`)
- Decisión: se ajusta la matriz, no el código. Arquitectura real: el móvil
  NO es cliente MQTT/CoAP (el gateway `edge_node/` es la parte MQTT;
  veredicto forense: `mqtt_local_subscriber.py` standalone + daemon con
  cursor). MQTT/CoAP directo en Flutter = peso muerto (nueva dependencia,
  permisos, batería) sin caso de uso en MVP.
- MQTT/CoAP móvil diferido a V2.0; si V2 lo retoma, este issue es la spec.
  Dashboard + badge + REST quedan como superficie canónica.
