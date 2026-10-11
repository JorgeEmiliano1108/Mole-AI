# 23: RNF-AI-02: Rendimiento de inferencia local MobileNetV2

Status: ready-for-agent

## Requisito

- **ID:** RNF-AI-02
- **Capa:** Agentes e IA
- **Tipo:** RNF
- **Texto:** La Red Neuronal Convolucional (MobileNetV2 ejecutada en TensorFlow Lite) en el borde debe ejecutar la predicción visual en <850 ms sin exceder un drenaje de batería del 4.5% por hora.

## Veredicto

❌ NO IMPLEMENTADO — Latencia medida pero no validada; sin medición de batería.

## Evidencia

- Modelo TFLite: `mobile/lib/features/vision/edge_ai.dart:25`.
- Stopwatch de latencia: `mobile/lib/features/vision/edge_ai.dart:115-127`.
- Test solo verifica `latencyMs >= 0.0`: `mobile/test/edge_ai_test.dart:47`.
- No hay medición de batería (`mAh`, `%/h`).
- PVU usa batería solo para routing (`mobile/lib/pvu/routing.dart:51-65`).

## Delta (matriz ideal vs. estado implementado)

El requisito establece dos cotas cuantitativas. El código mide latencia pero no la valida contra 850 ms, y carece de medición energética.

## Nota normativa / riesgo

Crítico para campo rural y sostenibilidad. Se recomienda harness con `adb shell dumpsys batterystats` o instrumentación nativa.

## Siguiente paso sugerido

Implementar benchmark de latencia con umbral 850 ms y medición de drenaje de batería; integrar a CI o release checklist.
