# Issue 19: Sincronizar docs con el código

Status: ready-for-agent
Sev: P2 · Área: docs · Fase: E

## Evidencia
- `docs/requisitos.md:52` RNF-01 SECURITY_0 vs spec `SECURITY_1 (heredada)` vs
  código JustWorks (`ble_provisioning.c:339-344`); RNF-13/RNF-16/RF-10 con estados
  distintos a la implementación; counts obsoletos (`README` 37 vs 44 tests, etc.).

## Problema
Docs que contradicen al código = decisiones futuras sobre premisas falsas.

## Aceptación
- `requisitos.md`, `README`s y spec alineados con la realidad verificada
  (estados FSM, counts de tests, modelo de seguridad BLE real).
- Checklist de sincronía docs↔código en la definición de done de cada fase.

## Compliance
Trazabilidad; `grill-with-docs` como gate.

## Comments
(none)
