# 04: RF-FE-04: Diagnóstico visual y Progressive Disclosure

Status: ready-for-agent

## Requisito

- **ID:** RF-FE-04
- **Capa:** Frontend
- **Tipo:** RF
- **Texto:** La interfaz debe mostrar el diagnóstico (mapas de calor o bounding boxes) junto con las recomendaciones agronómicas en un formato paso a paso, aplicando el principio de 'Divulgación Progresiva'.

## Veredicto

⚠️ PARCIAL — Recomendaciones y datos del diagnóstico OK; faltan mapas de calor, bounding boxes y Progressive Disclosure.

## Evidencia

- Recomendaciones: `mobile/lib/features/vision/diagnosis_screen.dart:335-365`.
- Historial: `mobile/lib/features/vision/diagnosis_history.dart:84-97`.
- No se encontró renderizado de heatmaps ni bounding boxes sobre la imagen.
- No hay componentes de expand/collapse por pasos.

## Delta (matriz ideal vs. estado implementado)

La UI muestra la información de una sola vez, condicionalmente, pero no aplica Progressive Disclosure ni visualizaciones de atención.

## Nota normativa / riesgo

Si el diagnóstico es bloqueado por `SafetyValidator`, se renderiza `SafetyBlockBanner` (`mobile/lib/core/safety_block_banner.dart:22-74`).

## Siguiente paso sugerido

Diseñar e implementar visualización de heatmaps/bounding boxes y Progressive Disclosure, o ajustar la matriz.

## Diferido a V2.0 — Acta F4 (2026-10-06, skills `triage` + `grill-with-docs`)
- Decisión: cosmético/UX-avanzado → V2.0 (mandato anti-refactorización del
  Code Freeze: prohibido extender alcance con interfaz no crítica).
- Fundamento técnico: el modelo edge (MobileNetV2 FP16, thr 0.70, cobertura
  ~15%) no expone mapas de atención utilizables; heatmaps exigirían
  instrumentación del intérprete + validación agronómica. Sin eso, un
  heatmap sería decoración (anti-teatro).
- Queda: recomendaciones + disclaimer + historial + `SafetyBlockBanner`
  (testeados). Reabrir solo con gate de campo que lo justifique.
