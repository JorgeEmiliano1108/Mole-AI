"""
Training Pipeline — CNN Fine-Tuning in Isolated Process

This module contains the pure function `fine_tune_model()` that runs inside
a ProcessPoolExecutor worker. It is completely decoupled from FastAPI's
event loop and can safely perform CPU-intensive operations.

Architecture:
  1. Load base Keras model (.h5 or MobileNetV2 transfer learning)
  2. Prepare dataset using tf.keras.utils.image_dataset_from_directory
  3. Fine-tune: freeze base layers, train classification head
  4. Convert result to TFLite for production inference
  5. Update labels.json with discovered classes
  6. Return results dict to the caller (vision_listener)

IMPORTANT: This function runs in a SEPARATE PROCESS via ProcessPoolExecutor.
Do NOT import FastAPI, asyncio, or any event-loop-dependent code here.
"""
import json
import logging
import os
import shutil
import time
from typing import Any, Dict

logger = logging.getLogger("ms1.training_pipeline")


def fine_tune_model(
    base_model_path: str,
    dataset_path: str,
    output_dir: str,
    labels_path: str,
    epochs: int = 5,
    batch_size: int = 16,
    learning_rate: float = 0.0001,
    image_size: int = 224,
    record_id: str = "",
) -> Dict[str, Any]:
    """
    Execute CNN fine-tuning in an isolated process.

    This function is designed to be called via ProcessPoolExecutor
    and does NOT interact with FastAPI or asyncio.

    Args:
        base_model_path: Path to the base Keras model (.h5) or "transfer_learning"
                         to use MobileNetV2 from tf.keras.applications.
        dataset_path:    Path to extracted dataset directory with class subfolders.
        output_dir:      Directory to save the fine-tuned model + TFLite output.
        labels_path:     Path to the existing labels.json file.
        epochs:          Number of training epochs.
        batch_size:      Training batch size.
        learning_rate:   Adam optimizer learning rate.
        image_size:      Input image dimension (square, e.g. 224).
        record_id:       Training record UUID for traceability.

    Returns:
        Dict with keys:
          - success (bool)
          - tflite_path (str): Path to the new .tflite model
          - labels_path (str): Path to the updated labels.json
          - metrics (dict): Training metrics {accuracy, loss, epochs_run}
          - classes (list): Class names discovered in the dataset
          - error (str): Error message if failed
    """
    start_time = time.time()
    result = {
        "success": False,
        "tflite_path": "",
        "labels_path": "",
        "metrics": {},
        "classes": [],
        "error": "",
        "record_id": record_id,
    }

    try:
        # Import TensorFlow here (inside the subprocess, not at module level)
        import tensorflow as tf
        import numpy as np

        logger.info(
            "training_started",
            extra={
                "record_id": record_id,
                "dataset_path": dataset_path,
                "epochs": epochs,
                "batch_size": batch_size,
            },
        )

        os.makedirs(output_dir, exist_ok=True)

        # ── Step 1: Prepare Dataset ──────────────────────────────────
        train_ds = tf.keras.utils.image_dataset_from_directory(
            dataset_path,
            validation_split=0.2,
            subset="training",
            seed=42,
            image_size=(image_size, image_size),
            batch_size=batch_size,
            label_mode="categorical",
        )

        val_ds = tf.keras.utils.image_dataset_from_directory(
            dataset_path,
            validation_split=0.2,
            subset="validation",
            seed=42,
            image_size=(image_size, image_size),
            batch_size=batch_size,
            label_mode="categorical",
        )

        class_names = train_ds.class_names
        num_classes = len(class_names)
        result["classes"] = class_names

        logger.info(
            "dataset_prepared",
            extra={
                "num_classes": num_classes,
                "class_names": class_names,
                "record_id": record_id,
            },
        )

        # Normalize pixel values to [0, 1]
        normalization = tf.keras.layers.Rescaling(1.0 / 255)
        train_ds = train_ds.map(lambda x, y: (normalization(x), y))
        val_ds = val_ds.map(lambda x, y: (normalization(x), y))

        # Prefetch for performance
        AUTOTUNE = tf.data.AUTOTUNE
        train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
        val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

        # ── Step 2: Load or Create Base Model ────────────────────────
        if os.path.exists(base_model_path) and base_model_path.endswith(".h5"):
            logger.info("loading_keras_model", extra={"path": base_model_path})
            base_model = tf.keras.models.load_model(base_model_path)
            # Rebuild classification head for potentially new class count
            model = _rebuild_head(base_model, num_classes, image_size)
        else:
            logger.info("using_transfer_learning", extra={"base": "MobileNetV2"})
            model = _build_mobilenetv2(num_classes, image_size)

        # ── Step 3: Compile & Train ──────────────────────────────────
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )

        logger.info("training_compile_done", extra={"record_id": record_id})

        # Train with early stopping to avoid overfitting
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor="val_accuracy",
                patience=3,
                restore_best_weights=True,
            ),
        ]

        history = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=epochs,
            callbacks=callbacks,
            verbose=0,  # Suppress per-epoch output in subprocess
        )

        # Extract final metrics
        final_accuracy = float(history.history["accuracy"][-1])
        final_val_accuracy = float(history.history["val_accuracy"][-1])
        final_loss = float(history.history["loss"][-1])
        epochs_run = len(history.history["accuracy"])

        result["metrics"] = {
            "accuracy": round(final_accuracy, 4),
            "val_accuracy": round(final_val_accuracy, 4),
            "loss": round(final_loss, 4),
            "epochs_run": epochs_run,
        }

        logger.info(
            "training_completed",
            extra={
                "record_id": record_id,
                "accuracy": final_accuracy,
                "val_accuracy": final_val_accuracy,
                "epochs_run": epochs_run,
            },
        )

        # ── Step 4: Save Keras + Convert to TFLite ───────────────────
        timestamp = int(time.time())
        keras_path = os.path.join(output_dir, f"cnn_finetuned_{timestamp}.h5")
        tflite_path = os.path.join(output_dir, f"cnn_finetuned_{timestamp}.tflite")

        model.save(keras_path)

        # TFLite conversion with float16 quantization for size reduction
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
        tflite_model = converter.convert()

        with open(tflite_path, "wb") as f:
            f.write(tflite_model)

        logger.info(
            "tflite_converted",
            extra={
                "keras_path": keras_path,
                "tflite_path": tflite_path,
                "tflite_size_mb": round(len(tflite_model) / (1024 * 1024), 2),
            },
        )

        # ── Step 5: Update labels.json ───────────────────────────────
        new_labels_path = os.path.join(output_dir, f"labels_{timestamp}.json")
        new_labels = _build_labels(class_names, labels_path)
        with open(new_labels_path, "w", encoding="utf-8") as f:
            json.dump(new_labels, f, indent=2, ensure_ascii=False)

        result["success"] = True
        result["tflite_path"] = tflite_path
        result["labels_path"] = new_labels_path

        elapsed = time.time() - start_time
        logger.info(
            "training_pipeline_success",
            extra={
                "record_id": record_id,
                "elapsed_seconds": round(elapsed, 1),
                "tflite_path": tflite_path,
            },
        )

    except Exception as e:
        result["error"] = str(e)
        logger.error(
            "training_pipeline_failed",
            extra={"record_id": record_id, "error": str(e)},
            exc_info=True,
        )

    return result


def _build_mobilenetv2(num_classes: int, image_size: int):
    """
    Build a transfer learning model using MobileNetV2 as the base.

    Strategy:
      - Freeze the convolutional base (pre-trained on ImageNet)
      - Add a custom classification head for our plant disease classes
      - This trains only the head (~5% of total params), fast even on CPU
    """
    import tensorflow as tf

    base = tf.keras.applications.MobileNetV2(
        input_shape=(image_size, image_size, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False  # Freeze base layers

    model = tf.keras.Sequential([
        base,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(num_classes, activation="softmax"),
    ])

    return model


def _rebuild_head(base_model, num_classes: int, image_size: int):
    """
    Rebuild the classification head of an existing model for a new class count.

    Removes the last Dense layer and replaces it with one matching num_classes.
    Freezes all layers except the last 2 (classification head).
    """
    import tensorflow as tf

    # Attempt to use the model up to the second-to-last layer
    try:
        # Find the last non-Dense layer to use as feature extractor
        feature_layers = []
        for layer in base_model.layers:
            feature_layers.append(layer)
            if isinstance(layer, tf.keras.layers.GlobalAveragePooling2D):
                break

        if not feature_layers:
            # Fallback: use transfer learning from scratch
            return _build_mobilenetv2(num_classes, image_size)

        # Build new model reusing the feature extraction layers
        inputs = tf.keras.Input(shape=(image_size, image_size, 3))
        x = inputs
        for layer in feature_layers:
            layer.trainable = False
            x = layer(x)

        x = tf.keras.layers.Dropout(0.3)(x)
        x = tf.keras.layers.Dense(128, activation="relu")(x)
        x = tf.keras.layers.Dropout(0.2)(x)
        outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)

        return tf.keras.Model(inputs=inputs, outputs=outputs)

    except Exception:
        # If head rebuild fails, fall back to transfer learning
        return _build_mobilenetv2(num_classes, image_size)


def _build_labels(class_names: list, existing_labels_path: str) -> dict:
    """
    Build an updated labels.json merging existing labels with new class names.

    New classes get a generic entry that the agronomist can later enrich.
    """
    # Load existing labels for reference
    existing = {}
    if os.path.exists(existing_labels_path):
        try:
            with open(existing_labels_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass

    # Build index-to-label mapping from class folder names
    # Class folder convention: "species_condition" (e.g. "tomate_tizon")
    new_labels = {}
    for idx, class_name in enumerate(class_names):
        # Try to match with existing labels
        matched = False
        for old_idx, old_info in existing.items():
            if isinstance(old_info, dict):
                old_condition = old_info.get("condition", "").lower().replace(" ", "_")
                old_species = old_info.get("species", "").lower().replace(" ", "_")
                folder_normalized = class_name.lower().replace(" ", "_")
                if folder_normalized in f"{old_species}_{old_condition}" or old_condition in folder_normalized:
                    new_labels[str(idx)] = old_info
                    matched = True
                    break

        if not matched:
            # Parse folder name (convention: "species_condition")
            parts = class_name.replace("_", " ").title().split(" ", 1)
            species = parts[0] if parts else "Desconocida"
            condition = parts[1] if len(parts) > 1 else "Desconocida"
            new_labels[str(idx)] = {
                "species": species,
                "condition": condition,
                "severity": "medium",
            }

    return new_labels
