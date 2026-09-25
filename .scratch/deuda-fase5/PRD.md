# PRD — Deuda técnica post-Fase 5 (auditoría consolidada)

**Origen**: auditoría dual (firmware+mobile, backend+infra) + validación cruzada contra código.
**Resultado**: 22 hallazgos TRUE, 4 descartados (infos `admin.dart` ya resueltas, `DB_URL` existe,
choque Kconfig falso, `0003` con reversa, "bare except" impreciso).
**Skills**: `triage` (labels), `to-issues` (este tracker), `enforce-compliance` (guardrails por issue).

## Orden de ejecución
- **Fase A** (P0, `ready-for-agent`): 01, 02 — integridad de primer arranque.
- **Fase B** (P0 seguridad/staging): 03, 04, 05 (05 `needs-info`: SMTP vs 501).
- **Fase C** (P1 firmware): 06–11 (10, 11 `needs-info`: chunking vs recorte, política MOCK).
- **Fase D** (P1/P2 CI/repro): 12–17.
- **Fase E** (P2 docs/ADRs): 18, 19.
- **Fase F** (mobile, con F6): 20, 21.

## Criterio de aceptación global
Build verde + tests del área + 0 warnings nuevos en archivos tocados
(guardrail: linters sin warnings, SonarQube 0 Blocker).

## Trazabilidad de decisiones `needs-info` (arquitecto)
- 05: ¿SMTP real o reset degradado?
- 10: ¿chunking FEE2 o spec recortada a 20 B?
- 11: ¿MOCK LTR390 con bits ON es política oficial?
- NVS sin cifrado: aceptado con ADR (issue 18) salvo veto.
- MQTT anonymous: riesgo aceptado Fase 2 (issue 04 lo documenta).
