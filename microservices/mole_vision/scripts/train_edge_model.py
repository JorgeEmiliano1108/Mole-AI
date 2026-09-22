#!/usr/bin/env python3
"""Runner P2: fine-tune MobileNetV2 + QAT + holdout campo (MRF02).

Uso (dentro del contenedor train con GPU, ver docs/analyses/pipeline-tflite.md):
    python scripts/train_edge_model.py \
        --dataset /data/PlantVillage/raw/color \
        --field-dir /data/field_photos \
        --holdout /data/field_holdout \
        --out /out/edge_mobilenetv2 --epochs 12 --quantize-aware

- Sin TF instalado falla con mensaje claro (no import parcial).
- Checkpointing: ModelCheckpoint guarda mejor val_accuracy (resume manual
  re-ejecutando con --base-model <h5>).
- Puerta P3: exige test_f1_macro en holdout (falla si < umbral).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "infrastructure", "adapters"))

HOLDOUT_F1_MIN = 0.70


def main() -> int:
    ap = argparse.ArgumentParser(description="Entrena el modelo edge real (P2)")
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--field-dir", default="", help="Fotos campo (extra_dirs)")
    ap.add_argument("--holdout", default="", help="Holdout campo (test_path)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--quantize-aware", action="store_true")
    ap.add_argument("--holdout-f1-min", type=float, default=HOLDOUT_F1_MIN)
    args = ap.parse_args()

    try:
        import tensorflow as tf  # noqa: F401
    except ImportError:
        print("ERROR: tensorflow no instalado. Usar contenedor train "
              "(requirements-train.txt + GPU).", file=sys.stderr)
        return 2

    from training_pipeline import fine_tune_model

    os.makedirs(args.out, exist_ok=True)
    result = fine_tune_model(
        base_model_path="transfer_learning",
        dataset_path=args.dataset,
        output_dir=args.out,
        labels_path=os.path.join(
            os.path.dirname(__file__), "..", "..", "models", "labels.json"),
        epochs=args.epochs,
        batch_size=args.batch_size,
        test_path=args.holdout,
        extra_dirs=[args.field_dir] if args.field_dir else None,
        quantize_aware=args.quantize_aware,
        record_id="edge-p2",
    )
    print(json.dumps(result.get("metrics", {}), indent=2))
    if not result.get("success"):
        print(f"FALLO: {result.get('error')}", file=sys.stderr)
        return 1
    f1 = (result.get("metrics") or {}).get("test_f1_macro")
    if args.holdout and f1 is not None and f1 < args.holdout_f1_min:
        print(f"PUERTA: test_f1_macro={f1} < {args.holdout_f1_min}. "
              f"No promover a APK.", file=sys.stderr)
        return 3
    print(f"OK: {result.get('tflite_path')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
