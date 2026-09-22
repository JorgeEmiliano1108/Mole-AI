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
    test_path: str = "",
    extra_dirs: list | None = None,
    quantize_aware: bool = False,
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
        test_path:       Optional holdout dir (class subfolders, p. ej. fotos de
                         campo) para matriz de confusión + F1-macro. Sin él no
                         hay gate de generalización (P1).
        extra_dirs:      Lista opcional de dirs extra (fotos con fondos ruidosos)
                         que se concatenan al train (mitiga fondo-de-laboratorio).
        quantize_aware:  Si True, envuelve el modelo con tfmot QAT antes de
                         entrenar (P2/P3; requiere `tensorflow-model-optimization`).

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

        # Crecimiento de VRAM bajo demanda (directriz 2026-09-20): sin GPU
        # es no-op; cuando el contenedor recupere GPU evita que TF acapare
        # los 6GB de golpe y repita el OOM.
        for _gpu in tf.config.list_physical_devices("GPU"):
            try:
                tf.config.experimental.set_memory_growth(_gpu, True)
            except RuntimeError:
                logger.debug("set_memory_growth no aplicable (GPU en uso)")

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

        # Normalización canónica [-1, 1]: IDÉNTICA a preprocessJpeg del APK
        # (mobile/lib/features/vision/edge_ai.dart). Divergencia train/serve
        # aquí = modelo sordo en producción. Test testigo:
        # tests/test_train_preprocess_parity.py
        normalization = tf.keras.layers.Rescaling(1.0 / 127.5, offset=-1)
        train_ds = train_ds.map(lambda x, y: (normalization(x), y))
        val_ds = val_ds.map(lambda x, y: (normalization(x), y))

        # Augmentation solo-train: clásica + fondos ruidosos vía extra_dirs
        # (mezcla de dominio contra el fondo-de-laboratorio de PlantVillage).
        augmentation = tf.keras.Sequential([
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.15),
            tf.keras.layers.RandomZoom(0.15),
            tf.keras.layers.RandomTranslation(0.1, 0.1),
            tf.keras.layers.RandomBrightness(0.2),
            tf.keras.layers.RandomContrast(0.2),
        ])
        # Prefetch acotado (revisión 2026-09-20): AUTOTUNE asfixia la RAM;
        # num_parallel_calls=4 y prefetch(2) son los únicos estranguladores
        # efectivos con tf.data. NOTA: `workers/use_multiprocessing` en fit()
        # se IGNORAN con tf.data — no añadirlos (regresión conocida).
        train_ds = train_ds.map(
            lambda x, y: (augmentation(x, training=True), y),
            num_parallel_calls=4,
        )
        train_ds = train_ds.prefetch(buffer_size=2)

        if extra_dirs:
            train_ds = _mix_extra_dirs(
                train_ds, train_ds.class_names, extra_dirs,
                image_size, batch_size, normalization,
            )
            train_ds = train_ds.shuffle(4096, seed=42)

        # SIN .cache() en train (directriz 2026-09-20): cachear congelaría el
        # augmentation y cada época vería las mismas transformaciones, matando
        # la varianza estocástica. Carga diferida pura desde disco.
        # Val SÍ se cachea a archivo (sin augmentation, 10k imgs): determinista
        # y sobrevive reinicios del contenedor.
        val_ds = val_ds.cache(
            os.path.join(output_dir, "val_cache")
        ).prefetch(buffer_size=2)

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
        # Pesos balanceados (dataset 152→5507/clase): se optimiza F1-macro,
        # no accuracy cruda (una clase mayoritaria la inflaría).
        from collections import Counter

        _counts = Counter()
        for _c in class_names:
            _d = os.path.join(dataset_path, _c)
            if os.path.isdir(_d):
                _counts[_c] = sum(
                    1 for _f in os.listdir(_d) if _is_img(_f)
                )
        _total = sum(_counts.values()) or 1
        class_weight = {
            i: _total / (len(class_names) * max(1, _counts.get(c, 0)))
            for i, c in enumerate(class_names)
        }

        if quantize_aware:
            try:
                import tensorflow_model_optimization as tfmot
            except ImportError as e:
                raise RuntimeError(
                    "quantize_aware=True requiere tensorflow-model-optimization"
                ) from e
            model = tfmot.quantization.keras.quantize_model(model)
            logger.info("QAT habilitado: fine-tune consciente de INT8")

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )

        logger.info("training_compile_done", extra={"record_id": record_id})

        # Train with early stopping to avoid overfitting.
        # ModelCheckpoint: resume = re-lanzar con --base-model <mejor .keras>.
        best_path = os.path.join(output_dir, "ckpt_best.keras")
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor="val_accuracy",
                patience=3,
                restore_best_weights=True,
            ),
            tf.keras.callbacks.ModelCheckpoint(
                filepath=best_path,
                monitor="val_accuracy",
                mode="max",
                save_best_only=True,
            ),
        ]

        history = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=epochs,
            callbacks=callbacks,
            class_weight=class_weight,
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

        # ── Step 3b: Holdout de campo (gate de generalización, P1) ──────
        # Si test_path se provee: matriz de confusión + F1-macro con numpy
        # (sin sklearn para no engordar la imagen). Sin holdout no hay gate.
        if test_path and os.path.isdir(test_path):
            test_ds = tf.keras.utils.image_dataset_from_directory(
                test_path,
                image_size=(image_size, image_size),
                batch_size=batch_size,
                label_mode="categorical",
                shuffle=False,
            )
            test_names = test_ds.class_names
            test_ds = test_ds.map(lambda x, y: (normalization(x), y))
            y_true, y_pred = [], []
            for tx, ty in test_ds:
                pr = model.predict(tx, verbose=0)
                y_true.extend(np.argmax(ty.numpy(), axis=1).tolist())
                # Realinea a índices canónicos por nombre de clase
                y_pred.extend([
                    class_names.index(test_names[i]) if test_names[i] in class_names else -1
                    for i in np.argmax(pr, axis=1).tolist()
                ])
            y_true = np.array(y_true)
            y_pred = np.array(y_pred)
            f1s = []
            for i in range(len(class_names)):
                tp = np.sum((y_true == i) & (y_pred == i))
                fp = np.sum((y_true != i) & (y_pred == i))
                fn = np.sum((y_true == i) & (y_pred != i))
                denom = 2 * tp + fp + fn
                f1s.append(0.0 if denom == 0 else 2 * tp / denom)
            result["metrics"]["test_f1_macro"] = round(float(np.mean(f1s)), 4)
            result["metrics"]["test_n"] = len(y_true)
            logger.info(
                "holdout_evaluated",
                extra={"test_f1_macro": result["metrics"]["test_f1_macro"],
                       "test_n": len(y_true)},
            )

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
        # Formato .keras (no .h5: h5py falla con modelos anidados en TF 2.16).
        keras_path = os.path.join(output_dir, f"cnn_finetuned_{timestamp}.keras")
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

        # INT8 PTQ con representative dataset (regla arquitectónica: si el
        # F1-macro INT8 cae >5% vs FP16, se descarta INT8 y se empaqueta FP16).
        # No tumba el run si falla: el entregable mínimo es el FP16 válido.
        int8_path = os.path.join(
            output_dir, f"cnn_finetuned_{timestamp}_int8.tflite")
        try:
            i8 = tf.lite.TFLiteConverter.from_keras_model(model)
            i8.optimizations = [tf.lite.Optimize.DEFAULT]
            i8.representative_dataset = lambda: representative_dataset(
                dataset_path, image_size)
            i8.target_spec.supported_ops = [
                tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
            i8.inference_input_type = tf.uint8
            i8.inference_output_type = tf.uint8
            int8_model = i8.convert()
            with open(int8_path, "wb") as f:
                f.write(int8_model)
            result["int8_path"] = int8_path
            result["metrics"]["int8_size_mb"] = round(
                len(int8_model) / (1024 * 1024), 2)
            logger.info("tflite_int8_converted", extra={"int8_path": int8_path})
        except Exception as e:
            logger.warning("tflite_int8_failed: %s", e)
            result["int8_path"] = ""
        result["metrics"]["fp16_size_mb"] = round(
            len(tflite_model) / (1024 * 1024), 2)

        # ── Step 5: Update labels.json ───────────────────────────────
        new_labels_path = os.path.join(output_dir, f"labels_{timestamp}.json")
        new_labels = _build_labels(class_names, labels_path)
        with open(new_labels_path, "w", encoding="utf-8") as f:
            json.dump(new_labels, f, indent=2, ensure_ascii=False)

        # labels.txt ordenado por índice: lo que consume el APK (MRF02).
        labels_txt_path = os.path.join(output_dir, f"labels_{timestamp}.txt")
        with open(labels_txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(class_names) + "\n")
        result["labels_txt_path"] = labels_txt_path

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


def _is_img(filename):
    """Extensiones de imagen, case-insensitive (PlantVillage usa .JPG)."""
    return filename.lower().endswith((".jpg", ".jpeg", ".png"))


def representative_dataset(dataset_path, image_size=224, n_samples=300):
    """Generador representativo para PTQ-INT8 (arquitectura dixit).

    Yield batches (1,H,W,3) float32 en norma canónica [-1,1], muestreo
    estratificado aproximado (round-robin por clase). Sin TF en import:
    el import vive dentro para no contaminar el servicio.
    """
    import random

    import tensorflow as tf

    per_class = []
    for c in sorted(os.listdir(dataset_path)):
        sub = os.path.join(dataset_path, c)
        if not os.path.isdir(sub):
            continue
        files = sorted(
            os.path.join(sub, f) for f in os.listdir(sub) if _is_img(f)
        )
        if files:
            per_class.append(files)
    if not per_class:
        raise ValueError(f"Sin imágenes en {dataset_path}")
    rng = random.Random(42)
    yielded = 0
    ci = 0
    while yielded < n_samples:
        files = per_class[ci % len(per_class)]
        ci += 1
        path = rng.choice(files)
        try:
            raw = tf.io.read_file(path)
            img = tf.image.decode_jpeg(raw, channels=3)
        except (tf.errors.OpError, OSError, ValueError):
            logger.warning("representative: salto %s (ilegible)", path)
            continue
        img = tf.image.resize(img, [image_size, image_size])
        img = tf.cast(img, tf.float32) * (1.0 / 127.5) - 1.0
        yield [tf.expand_dims(img, 0)]
        yielded += 1


def _mix_extra_dirs(train_ds, canon_names, extra_dirs, image_size,
                    batch_size, normalization):
    """Mezcla fotos de campo (fondos ruidosos) al train con ÍNDICES canónicos.

    Solo acepta subcarpetas cuyo nombre existe en `canon_names`
    (orden PlantVillage); el resto se ignora con warning. Sin esta
    realineación, `image_dataset_from_directory` reindexaría y corrompería
    las etiquetas.
    """
    import tensorflow as tf

    def _decode(path, label):
        img = tf.io.read_file(path)
        img = tf.image.decode_jpeg(img, channels=3)
        img = tf.image.resize(img, [image_size, image_size])
        img = tf.cast(img, tf.float32)
        return normalization(img), tf.one_hot(label, len(canon_names))

    for extra in extra_dirs:
        if not os.path.isdir(extra):
            logger.warning("extra_dir inexistente: %s", extra)
            continue
        paths, labels = [], []
        for c in sorted(os.listdir(extra)):
            if c not in canon_names:
                logger.warning("extra_dir: clase '%s' fuera del canónico, se ignora", c)
                continue
            sub = os.path.join(extra, c)
            if not os.path.isdir(sub):
                continue
            for f in sorted(os.listdir(sub)):
                if _is_img(f):
                    paths.append(os.path.join(sub, f))
                    labels.append(canon_names.index(c))
        if not paths:
            continue
        extra_ds = tf.data.Dataset.from_tensor_slices((paths, labels))
        extra_ds = extra_ds.map(_decode, num_parallel_calls=tf.data.AUTOTUNE)
        extra_ds = extra_ds.batch(batch_size)
        train_ds = train_ds.concatenate(extra_ds)
        logger.info("extra_dir mezclado: %s (%d imgs)", extra, len(paths))
    return train_ds


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
