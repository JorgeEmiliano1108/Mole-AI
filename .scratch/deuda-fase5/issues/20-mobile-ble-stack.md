# Issue 20: Stack BLE real en Flutter

Status: ready-for-agent
Sev: P1 · Área: mobile · Fase: F

## Evidencia
- `pubspec.yaml:30-56` sin `flutter_blue_plus/permission_handler`;
  `AndroidManifest.xml:8-10` sin `BLUETOOTH_SCAN/CONNECT/ACCESS_FINE_LOCATION`
  (spec §5:112-113 los exige).
- Solo existe decoder puro + badge; sin scan/connect/CCC `0x0001`/MTU≥64.

## Problema
Fase 5 "cerrada" sin stack BLE real: la app no puede leer FEE2 en campo.

## Aceptación
- Servicio BLE (scan filtrado por `mole-agri-sensor`/FEE0, connect, READ FEE2,
  subscribe NOTIFY, MTU≥64) + permisos runtime + telemetría con `source=bleLive`.
- Tests con fake-adapter (incl. timeout 5 s); `analyze` 0 issues.

## Compliance
Contrato visual F5 ya existe (badge); este issue lo alimenta con datos reales.

## Comments
(none)
