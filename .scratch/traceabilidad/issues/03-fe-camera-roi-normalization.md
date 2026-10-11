# 03: RF-FE-03: Cámara, recorte de ROI y normalización

Status: ready-for-human

## Requisito

- **ID:** RF-FE-03
- **Capa:** Frontend
- **Tipo:** RF
- **Texto:** El sistema debe capturar fotografías desde la cámara, permitir el recorte de la Región de Interés (ROI) y aplicar normalización a la imagen antes de la inferencia.

## Veredicto

⚠️ PARCIAL — Cámara y normalización OK; recorte interactivo de ROI no implementado.

## Evidencia

- `mobile/pubspec.yaml:41` incluye `image_picker: ^1.2.3`.
- Captura: `mobile/lib/features/vision/diagnosis_screen.dart:159-161`.
- Normalización 224×224 y rango [-1,1]: `mobile/lib/features/vision/edge_ai.dart:70-86`.
- Tests normalización: `mobile/test/edge_ai_test.dart:19-31`.
- Guía visual estática sin ROI: `mobile/lib/features/vision/diagnosis_screen.dart:387-398` (comentario 'Sin segmentación en v1').

## Delta (matriz ideal vs. estado implementado)

Solo existe guía visual de encuadre; no hay recorte ni segmentación interactiva.

## Nota normativa / riesgo

MASVS-STORAGE: fotos pendientes se escriben en directorio privado (`mobile/lib/core/offline_store.dart:129`).

## Siguiente paso sugerido

Implementar recorte/selección interactiva de ROI o documentar que queda fuera del MVP.

## Veredicto actualizado Wave F3 (2026-10-06): CUMPLE
Recorte ROI interactivo implementado: `roi_crop.dart` (`RoiRect` + `cropRoi`
con clamp, mínimo 64px, `ArgumentError` ante basura) + bottom-sheet
`RoiCropSheet` (arrastrar + slider + Confirmar/Cancelar; cancelar = frame
completo) cableado en `_pick` antes del ruteo PVU. Tests
`f3_crop_capture_test.dart`. Skills `tdd` + `grill-with-docs` (contrato §5
intacto: crop es cliente).
