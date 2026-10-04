# 03: C3: Implementar harness de drenaje de batería

Status: ready-for-human

## Requisito

Medir el porcentaje de batería consumido por hora durante un bucle de inferencias en Android.

## Acceptance criteria

- [ ] MethodChannel Dart ↔ Kotlin que lee `BatteryManager`.
- [ ] Test de integración que corre inferencias durante N minutos y calcula `%/h`.
- [ ] Script Python para procesar el reporte del dispositivo.
- [ ] Documentación de que la validación oficial se hace en dispositivo gama baja.

## Blocked by

- `02-edge-latency-harness`.

## Notas

No se agregan dependencias de terceros; el channel es código propio.

