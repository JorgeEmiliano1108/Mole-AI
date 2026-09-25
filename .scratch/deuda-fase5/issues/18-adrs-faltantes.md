# Issue 18: ADRs faltantes (target, IRAM, NVS, DB_*, MQTT)

Status: ready-for-agent
Sev: P2 · Área: docs · Fase: E

## Evidencia
- `docs/adr/` solo tiene 0002–0006. Faltan actas para decisiones ya tomadas:
  target ESP32 (vs S3), `-Os` + `NO_IRAM_OPT` (`sdkconfig.defaults:29-34`),
  NVS sin cifrado (`:11-15`), canon `DB_*`, `.env.example` único, riesgo MQTT Fase 2.

## Problema
Decisiones vinculantes sin acta; futuros cambios las revertirán por accidente.

## Aceptación
- Un ADR por decisión (`docs/adr/NNNN-*.md`, formato del repo): contexto,
  decisión, consecuencias, fecha. Incluye el ADR de riesgo MQTT (issue 04).

## Compliance
Trazabilidad ISO/IEC 25001.

## Comments
(none)
