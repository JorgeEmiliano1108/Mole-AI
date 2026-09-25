# Issue 10: FEE2 chunking MTU vs recorte de spec

Status: needs-info
Sev: P1 · Área: firmware+mobile · Fase: C

## Evidencia
- `ble_provisioning.c:400-414` `ble_fee2_publish`: `notify` directo sin chequeo MTU
  ni fragmentación `[seq][total]` exigida en spec §3.
- `fee2_frame.h:21-22` trama máx 31 B > MTU-23 (útil ~20 B).
- `ble_telemetry.dart:140-169` `BleFrameAssembler` exige header que el firmware jamás emite.

## Problema
Truncado en radios/MTU antiguas; assembler Dart incompatible con el wire real.

## Aceptación (según veredicto)
- **Opción chunking**: implementar `[seq][total][chunk]` + assembler real (+ código/IRAM).
- **Opción recorte**: spec garantiza ≤20 B siempre; assembler se simplifica a trama única.
- Bloqueado hasta veredicto (ver PRD). Contradice nada de Fase 5 (caso típico 19 B cabe).

## Compliance
Interoperabilidad BLE real (spec §3 vinculante).

## Comments
(none)
