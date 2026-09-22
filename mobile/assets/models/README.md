# Modelos Edge AI (MRF02)

## `plant_mobilenetv2_38.tflite` (4.8 MB) — FP16 real (PlantVillage 38 clases)

- Firma: input `(1,224,224,3)` float32 normalizado `[-1,1]` → output `(1,38)` softmax.
- Origen: fine-tune MobileNetV2 (pipeline P1/P2) + export FP16 TF 2.18.
  Métricas holdout-proxy: F1-macro 0.5172 (optimista; gate campo pendiente).
- INT8 descartado dos veces: (1) regla >5% no aplica (INT8 F1=0.5373, sin caída),
  pero (2) el contrato Dart es f32 (`Float32List` en `edge_ai.dart`) y el modelo
  uint8 rompería en dispositivo → FP16 conserva el contrato intacto.
- `labels.txt`: 38 clases en orden canónico (= índice de salida).

## Umbral y fallback

- `confidenceThreshold = 0.70`: bajo él, la foto va a `diag_queue` (SQLite) y al
  servidor (LLM+RAG). Curva medida: thr 0.70 → precisión 0.94, cobertura ~15%.
- Historial: el stand-in aleatorio (`mobilenetv2_integration.tflite`, FC+softmax
  construido a mano con flatbuffers) sirvió para cablear `tflite_flutter` y el
  fallback; retirado del bundle al llegar el modelo real.
