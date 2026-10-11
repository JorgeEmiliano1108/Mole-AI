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

## Diferido a V2.0 — Acta F4 (2026-10-06, skills `triage` + `grill-with-docs`)
- Decisión de usuario (recorte de scope MVP): telemetría **solo-servidor**
  para el MVP; stack BLE real (scan/connect FEE2, permisos runtime,
  `source=bleLive`) pasa a post-MVP con este issue como especificación.
- Criterio: sin hardware BLE en campo durante el MVP, el stack no es
  verificable (anti-teatro: prohibido implementar sin prueba campo).
- Alcance diferido íntegro: servicio BLE + permisos + tests fake-adapter.
  Ver también `mvp-17-ble-live` (gemelo firmware+app, misma acta).
- Riesgo aceptado: app ciega a FEE2 en vivo; mitigación: badge
  `telemetry_badge.dart` + fallback `telemetry/latest/` documentados y
  testeados. Status queda `ready-for-agent` (cola V2, no MVP).
