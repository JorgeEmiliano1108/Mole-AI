"""
Vision Training Listener — Redis Pub/Sub event-driven fine-tuning orchestrator.

Subscribes to `mole:training:new_asset` and processes events with
`asset_type == "image"`. Ignores document events (those are for MS2/RAG).

Architecture:
  - Runs as an asyncio.Task started from FastAPI's lifespan
  - Downloads ZIP from MinIO (S3Downloader)
  - Submits fine-tuning to ProcessPoolExecutor (separate process, no GIL)
  - Hot-swaps the TFLite model in the running adapter after training
  - Publishes status loopback to `mole:training:status`

Concurrency Contract:
  - The listener itself runs on the FastAPI event loop (lightweight I/O)
  - The training function runs in a SEPARATE PROCESS via ProcessPoolExecutor
  - Only ONE training job runs at a time (max_workers=1)
  - FastAPI continues serving inference requests during training

LFPDPPP Compliance:
  - No PII in Redis events or logs
  - Training datasets are cleaned from /tmp after processing
"""
import asyncio
import json
import logging
import traceback
from concurrent.futures import ProcessPoolExecutor

from app.core.config import settings

logger = logging.getLogger("ms1.vision_listener")

# ── Redis channel constants ──────────────────────────────────────────────
CHANNEL_NEW_ASSET = "mole:training:new_asset"
CHANNEL_STATUS = "mole:training:status"

# ── Process pool for training (module-level singleton) ───────────────────
# max_workers=1: Only one training at a time to avoid CPU/RAM saturation
_training_executor = ProcessPoolExecutor(max_workers=1)


async def start_vision_listener() -> asyncio.Task:
    """
    Start the vision training listener as a background asyncio.Task.

    Call this from FastAPI's lifespan `startup` event.
    Returns the task handle for cleanup in `shutdown`.
    """
    task = asyncio.create_task(_listener_loop(), name="vision_training_listener")
    logger.info("vision_listener_started", extra={"channel": CHANNEL_NEW_ASSET})
    return task


async def _listener_loop():
    """
    Main listener loop: subscribes to Redis and processes image events.

    Reconnects automatically on connection failures with exponential backoff.
    Filters events: only processes asset_type == "image".
    """
    import redis.asyncio as aioredis

    backoff = 1
    max_backoff = 60

    while True:
        try:
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe(CHANNEL_NEW_ASSET)
            logger.info("redis_pubsub_subscribed", extra={"channel": CHANNEL_NEW_ASSET})
            backoff = 1  # Reset on success

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    payload = json.loads(message["data"])
                    asset_type = payload.get("asset_type", "")
                    record_id = payload.get("record_id", "")
                    s3_key = payload.get("s3_key", "")

                    # ── FILTER: Only process image assets ────────────
                    if asset_type != "image":
                        logger.debug(
                            "event_ignored",
                            extra={
                                "asset_type": asset_type,
                                "reason": "not an image asset",
                            },
                        )
                        continue

                    logger.info(
                        "training_event_received",
                        extra={
                            "event_type": payload.get("event_type"),
                            "asset_type": asset_type,
                            "record_id": record_id,
                            "s3_key": s3_key,
                        },
                    )

                    await _process_image_training(payload, r)

                except json.JSONDecodeError as e:
                    logger.error("invalid_event_json", extra={"error": str(e)})
                except Exception as e:
                    logger.error(
                        "event_processing_error",
                        extra={"error": str(e), "traceback": traceback.format_exc()},
                    )

        except asyncio.CancelledError:
            logger.info("vision_listener_cancelled")
            break
        except Exception as e:
            logger.error(
                "redis_connection_error",
                extra={"error": str(e), "backoff": backoff},
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)


async def _process_image_training(payload: dict, redis_client) -> None:
    """
    Full fine-tuning pipeline for a single image training event.

    Steps:
      1. Download ZIP from MinIO
      2. Submit fine-tuning to ProcessPoolExecutor (non-blocking)
      3. Hot-swap TFLite model if training succeeds
      4. Publish status loopback to Redis
      5. Cleanup temporary files
    """
    record_id = payload.get("record_id", "")
    s3_key = payload.get("s3_key", "")
    s3_bucket = payload.get("s3_bucket", settings.TRAINING_BUCKET_NAME)

    logger.info("vision_pipeline_start", extra={"record_id": record_id, "s3_key": s3_key})

    dataset_path = None
    try:
        # ── Step 1: Download and extract ZIP from MinIO ──────────────
        from app.infrastructure.adapters.s3_downloader import S3Downloader

        downloader = S3Downloader()
        loop = asyncio.get_event_loop()

        # Run blocking download in thread pool (I/O bound, not CPU)
        dataset_path = await loop.run_in_executor(
            None, downloader.download_and_extract_zip, s3_key, s3_bucket
        )
        logger.info(
            "dataset_downloaded",
            extra={"record_id": record_id, "dataset_path": dataset_path},
        )

        # ── Step 2: Submit fine-tuning to ProcessPoolExecutor ────────
        from app.infrastructure.adapters.training_pipeline import fine_tune_model

        training_result = await loop.run_in_executor(
            _training_executor,
            fine_tune_model,
            settings.CNN_BASE_MODEL_PATH,
            dataset_path,
            settings.TRAINING_OUTPUT_DIR,
            settings.CNN_LABELS_PATH,
            settings.TRAINING_EPOCHS,
            settings.TRAINING_BATCH_SIZE,
            settings.TRAINING_LEARNING_RATE,
            settings.TRAINING_IMAGE_SIZE,
            record_id,
        )

        if not training_result.get("success"):
            raise RuntimeError(
                f"Training failed: {training_result.get('error', 'Unknown error')}"
            )

        logger.info(
            "training_result_received",
            extra={
                "record_id": record_id,
                "metrics": training_result.get("metrics"),
                "classes": training_result.get("classes"),
                "tflite_path": training_result.get("tflite_path"),
            },
        )

        # ── Step 3: Hot-swap TFLite model ────────────────────────────
        new_tflite_path = training_result.get("tflite_path", "")
        new_labels_path = training_result.get("labels_path", "")

        if new_tflite_path:
            _hot_swap_model(new_tflite_path, new_labels_path)

        # ── Step 4: Publish INDEXED status ───────────────────────────
        await _publish_status(
            redis_client,
            record_id=record_id,
            status="INDEXED",
            extra={
                "metrics": training_result.get("metrics", {}),
                "classes_count": len(training_result.get("classes", [])),
            },
        )

        logger.info(
            "vision_pipeline_success",
            extra={
                "record_id": record_id,
                "tflite_path": new_tflite_path,
                "metrics": training_result.get("metrics"),
            },
        )

    except Exception as e:
        logger.error(
            "vision_pipeline_failed",
            extra={
                "record_id": record_id,
                "s3_key": s3_key,
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )
        await _publish_status(
            redis_client,
            record_id=record_id,
            status="FAILED",
            error_message=str(e),
        )

    finally:
        # ── Step 5: Cleanup temporary dataset files ──────────────────
        if dataset_path:
            from app.infrastructure.adapters.s3_downloader import S3Downloader
            # Clean the parent /tmp/training_<uuid>/ directory
            import os
            parent_dir = os.path.dirname(dataset_path)
            S3Downloader.cleanup(parent_dir)


def _hot_swap_model(tflite_path: str, labels_path: str) -> None:
    """
    Hot-swap the TFLite model in the running FastAPI process.

    This replaces the singleton vision adapter in dependencies.py
    without requiring a container restart.
    """
    try:
        from app.infrastructure.adapters.tflite_adapter import TFLiteVisionAdapter, TFLITE_AVAILABLE
        import app.api.dependencies as deps

        if not TFLITE_AVAILABLE:
            logger.warning("tflite_not_available_for_hotswap")
            return

        # Create new adapter with the fine-tuned model
        new_adapter = TFLiteVisionAdapter(
            model_path=tflite_path,
            labels_path=labels_path if labels_path else None,
        )

        if new_adapter.is_ready():
            # Atomic swap of the singleton
            old_adapter = deps._vision_adapter
            deps._vision_adapter = new_adapter
            logger.info(
                "model_hot_swapped",
                extra={
                    "new_model": tflite_path,
                    "new_labels": labels_path,
                    "old_model": getattr(old_adapter, "model_path", "unknown"),
                },
            )
        else:
            logger.error("new_model_not_ready", extra={"path": tflite_path})

    except Exception as e:
        logger.error(
            "hot_swap_failed",
            extra={"tflite_path": tflite_path, "error": str(e)},
        )


async def _publish_status(
    redis_client,
    record_id: str,
    status: str,
    error_message: str = "",
    extra: dict | None = None,
) -> None:
    """
    Publish a training status update to Redis for Django to consume.

    Channel: mole:training:status
    Payload: {record_id, status, asset_type, error_message, ...extra}
    """
    payload = {
        "event_type": "training.status_update",
        "record_id": record_id,
        "asset_type": "image",
        "status": status,
        "error_message": error_message,
    }
    if extra:
        payload.update(extra)

    try:
        await redis_client.publish(CHANNEL_STATUS, json.dumps(payload))
        logger.info(
            "status_published",
            extra={"channel": CHANNEL_STATUS, "record_id": record_id, "status": status},
        )
    except Exception as e:
        logger.error(
            "status_publish_failed",
            extra={"record_id": record_id, "error": str(e)},
        )
