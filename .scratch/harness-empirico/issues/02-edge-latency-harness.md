# 02: C2: Implementar harness de latencia Edge AI

Status: ready-for-human

## Requisito

Instrumentar la inferencia local para medir P50/P95/P99 de preprocess + run + threshold y comparar contra 850 ms.

## Acceptance criteria

- [ ] `InstrumentedEdgeInterpreter` en `mobile/lib/features/vision/benchmark/` que decora `EdgeInterpreter`.
- [ ] Test de integración que ejecuta múltiples iteraciones y genera reporte.
- [ ] Reporte JSON con estadísticas y veredicto pass/fail contra 850 ms.
- [ ] No impacto en código productivo cuando no se usa el harness.

## Blocked by

- `01-harness-protocol`.

## Notas

Usar `integration_test` y `Stopwatch` (sin nuevas dependencias).

