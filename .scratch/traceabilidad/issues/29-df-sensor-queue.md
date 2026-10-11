# 29: RF-DF-01: Captura pasiva de métricas ESP32 → móvil y cola local

Status: ready-for-agent

## Requisito

- **ID:** RF-DF-01
- **Capa:** Flujo de datos y sincronización
- **Tipo:** RF
- **Texto:** El sistema debe captar pasivamente las métricas de los sensores desde el ESP32 hacia el móvil y almacenarlas temporalmente en una cola de mensajes local.

## Veredicto

⚠️ PARCIAL — ESP32 publica BLE FEE2 y Flutter decodifica, pero falta scan/subscribe en app; `telemetry_cache` es caché de lectura, no cola de reenvío.

## Evidencia

- ESP32 publica FEE2: `microservices/esp32_node/main/main.c:819-830`, `fee2_frame.c:30-94`.
- Flutter decodifica: `mobile/lib/features/ble/ble_telemetry.dart:73-137`.
- Caché local: `mobile/lib/core/offline_db.dart:59` (`telemetry_cache`).
- Edge gateway MQTT: `edge_node/mqtt_local_subscriber.py:86-104`.

## Delta (matriz ideal vs. estado implementado)

La app no implementa scan/connect/subscribe a `0xFEE2` (`gatt-fee2-spec.md:110-119` indica 'sin código en esta fase'). La cola local (`diag_queue`) es solo para fotos.

## Nota normativa / riesgo

IFT-016: BLE no transporta PII/token. Path servidor usa TLS.

## Siguiente paso sugerido

Implementar scan/subscribe BLE FEE2 en Flutter y convertir `telemetry_cache` en cola de reenvío, o ajustar la matriz.
