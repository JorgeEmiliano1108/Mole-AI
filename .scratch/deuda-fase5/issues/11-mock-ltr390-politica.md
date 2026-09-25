# Issue 11: Política MOCK LTR390 (bits ON con dato falso)

Status: needs-info
Sev: P1 · Área: firmware · Fase: C

## Evidencia
- `main.c:773-776` `else if(!s_ltr390){ l=8500.0f; u=3.5f; valid|=0x0C; }` —
  inyección permanente indistinguible de medida real (`fee2_encode`/edge-batch).
- `docs/requisitos.md:23` RF-10 lo normaliza como "Cumple".

## Problema
Enmascara `dg`; el backend y la app creen dato real.

## Aceptación (según veredicto)
- **Opción oficial**: documentar mock como política + badge/plaga visual que lo distinga.
- **Opción honesta**: bits apagados + `dg` real cuando no hay sensor.
- Bloqueado hasta veredicto (ver PRD).

## Compliance
Integridad del dato ambiental (NOM-059: decisiones sobre especies con datos falsos).

## Comments
(none)
