# 07: RNF-FE-03: Prevención de errores en captura de imágenes

Status: ready-for-human

## Requisito

- **ID:** RNF-FE-03
- **Capa:** Frontend
- **Tipo:** RNF
- **Texto:** La interfaz de captura de imágenes debe aplicar validación en tiempo real (ej. iluminación insuficiente) para prevenir inputs erróneos hacia el modelo, alineándose con heurísticas de usabilidad.

## Veredicto

❌ NO IMPLEMENTADO — Sin validación de calidad de imagen.

## Evidencia

- Guía visual estática: `mobile/lib/features/vision/diagnosis_screen.dart:387-398`.
- `preprocessJpeg` lanza `ArgumentError` solo si el JPEG no decodifica (`mobile/lib/features/vision/edge_ai.dart:72`).

## Delta (matriz ideal vs. estado implementado)

No hay validación de iluminación, desenfoque u orientación. Tesis tampoco lo documenta.

## Nota normativa / riesgo

Inputs de baja calidad pueden degradar confianza del modelo y aumentar falsos negativos agrícolas.

## Siguiente paso sugerido

Implementar validación en tiempo real de iluminación/desenfoque u otras heurísticas de calidad.

## Veredicto actualizado Wave F3 (2026-10-06): CUMPLE
`capture_check.dart`: luminancia media + varianza del Laplaciano, umbrales
conservadores, guía accionable; gate en `_pick` (rechazo = mensaje, nada se
encola/infiere). Hallazgo: el decoder `image` lanza `RangeError` ante basura
(no null) — normalizado. EXIF lo aplica el decoder v4. Skill `tdd`.
