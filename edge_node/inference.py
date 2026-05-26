# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
#
# AVISO DE PROPIEDAD INTELECTUAL:
# Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
# Queda estrictamente prohibida la copia, modificación, distribución,
# sublicenciamiento o uso comercial de este código, total o parcialmente,
# sin la autorización expresa y por escrito de los titulares del Copyright.
#
# Cualquier uso no autorizado será perseguido conforme a la Ley Federal
# del Derecho de Autor (México) y tratados internacionales aplicables.
# =============================================================================
"""
inference.py — Mole.AI Edge Node
==================================
Captures an image, runs the TFLite pH regression model (HSV colorimetry),
and enqueues the result alongside the latest telemetry in local SQLite.

Usage:
  python inference.py --device-id ESP32-001 --plant-id planta_maiz_01

The ph_cnn float (e.g. 6.3) is then synced to Django by
store_forward_daemon.py alongside the sensor telemetry.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [INFERENCE] %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
MODEL_PATH = Path(os.getenv("TFLITE_MODEL_PATH", "models/ph_regression.tflite"))
INPUT_SIZE = (224, 224)   # Adjust to match your TFLite model's input shape


# ── TFLite runner ─────────────────────────────────────────────────────────────

def load_interpreter():
    """Load TFLite interpreter. Falls back gracefully if model file missing."""
    try:
        import tflite_runtime.interpreter as tflite
        interpreter = tflite.Interpreter(model_path=str(MODEL_PATH))
        interpreter.allocate_tensors()
        logger.info("TFLite model loaded from %s", MODEL_PATH)
        return interpreter
    except ImportError:
        logger.warning("tflite_runtime not installed — using mock inference.")
        return None
    except Exception as e:
        logger.error("Failed to load TFLite model: %s", e)
        return None


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Load image, convert to HSV colour space, resize, normalise.
    The model expects HSV input — this matches the colorimetry training pipeline.
    """
    img = Image.open(image_path).convert("RGB")
    img = img.resize(INPUT_SIZE)
    # Convert RGB → HSV using PIL/numpy
    import colorsys
    arr = np.array(img, dtype=np.float32) / 255.0
    hsv = np.zeros_like(arr)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            hsv[i, j] = colorsys.rgb_to_hsv(*arr[i, j])
    return np.expand_dims(hsv, axis=0).astype(np.float32)


def run_inference(interpreter, image_path: str) -> float:
    """Run TFLite model and return continuous pH float (regression output)."""
    if interpreter is None:
        # Development mock — returns a plausible value for testing
        import random
        mock_ph = round(random.uniform(5.5, 7.5), 2)
        logger.warning("Mock inference active — ph_cnn=%.2f", mock_ph)
        return mock_ph

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_tensor = preprocess_image(image_path)
    interpreter.set_tensor(input_details[0]['index'], input_tensor)
    interpreter.invoke()

    output = interpreter.get_tensor(output_details[0]['index'])
    ph_value = float(output[0][0])
    ph_value = max(0.0, min(14.0, round(ph_value, 2)))  # Clamp to valid range
    logger.info("TFLite inference complete — ph_cnn=%.2f", ph_value)
    return ph_value


# ── Integration with Store-and-Forward ────────────────────────────────────────

def enqueue_cnn_result(
    device_id: str,
    plant_id: str,
    ph_cnn: float,
    sensors: list[dict] | None = None,
) -> None:
    """Persist inference result to local SQLite for daemon sync."""
    from store_forward_daemon import enqueue_reading, init_db
    con = init_db()
    enqueue_reading(
        con,
        device_id=device_id,
        plant_id=plant_id,
        sensors=sensors or [],
        ph_cnn=ph_cnn,
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )
    logger.info("CNN result enqueued — device=%s plant=%s ph_cnn=%.2f", device_id, plant_id, ph_cnn)


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mole.AI TFLite pH Inference")
    parser.add_argument("--image",     required=True,  help="Path to leaf image")
    parser.add_argument("--device-id", required=True,  help="ESP32 device ID")
    parser.add_argument("--plant-id",  required=True,  help="Plant identifier")
    parser.add_argument("--sensors",   default="[]",   help="JSON sensor array from ESP32")
    args = parser.parse_args()

    interpreter = load_interpreter()
    ph_cnn = run_inference(interpreter, args.image)

    try:
        sensors = json.loads(args.sensors)
    except json.JSONDecodeError:
        sensors = []

    enqueue_cnn_result(
        device_id=args.device_id,
        plant_id=args.plant_id,
        ph_cnn=ph_cnn,
        sensors=sensors,
    )
