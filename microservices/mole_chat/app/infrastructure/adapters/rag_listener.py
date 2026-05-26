"""
RAG Training Listener — Redis Pub/Sub event-driven ingestion pipeline.

Subscribes to `mole:training:new_asset` channel and processes incoming
training documents by:
  1. Downloading PDF from MinIO (S3Downloader)
  2. Extracting text (pypdf)
  3. Chunking (RecursiveCharacterTextSplitter)
  4. Computing embeddings (sentence-transformers)
  5. Inserting into PostgreSQL/pgvector (PgVectorStore)
  6. Publishing status loopback to `mole:training:status`

Architecture:
  - Runs as an asyncio.Task started from FastAPI's lifespan
  - Heavy CPU work (embedding) is offloaded to thread pool via run_in_executor
  - Redis subscription uses redis.asyncio for non-blocking I/O
  - Does NOT block FastAPI's event loop

LFPDPPP Compliance:
  - No PII is stored in pgvector (only document chunks + metadata)
  - PDFs are processed in-memory, never persisted to disk
  - Status events contain only record_id and status (no PII)
"""
import asyncio
import io
import json
import logging
import traceback
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.core.config import settings

logger = logging.getLogger("ms2.rag_listener")

# ── Redis channel constants ──────────────────────────────────────────────
CHANNEL_NEW_ASSET = "mole:training:new_asset"
CHANNEL_STATUS = "mole:training:status"


async def start_rag_listener() -> asyncio.Task:
    """
    Start the RAG listener as a background asyncio.Task.

    Call this from FastAPI's lifespan `startup` event.
    Returns the task handle for cleanup in `shutdown`.
    """
    task = asyncio.create_task(_listener_loop(), name="rag_training_listener")
    logger.info("rag_listener_started", extra={"channel": CHANNEL_NEW_ASSET})
    return task


async def _listener_loop():
    """
    Main listener loop: subscribes to Redis and processes events.

    Reconnects automatically on connection failures with exponential backoff.
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
            backoff = 1  # Reset backoff on successful connection

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    payload = json.loads(message["data"])
                    logger.info(
                        "training_event_received",
                        extra={
                            "event_type": payload.get("event_type"),
                            "asset_type": payload.get("asset_type"),
                            "record_id": payload.get("record_id"),
                            "s3_key": payload.get("s3_key"),
                        },
                    )

                    # Only process document assets (PDFs for RAG)
                    if payload.get("asset_type") == "document":
                        await _process_document(payload, r)
                    else:
                        logger.info(
                            "skipping_non_document_asset",
                            extra={"asset_type": payload.get("asset_type")},
                        )

                except json.JSONDecodeError as e:
                    logger.error("invalid_event_json", extra={"error": str(e)})
                except Exception as e:
                    logger.error(
                        "event_processing_error",
                        extra={"error": str(e), "traceback": traceback.format_exc()},
                    )

        except asyncio.CancelledError:
            logger.info("rag_listener_cancelled")
            break
        except Exception as e:
            logger.error(
                "redis_connection_error",
                extra={"error": str(e), "backoff": backoff},
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)


async def _process_document(payload: dict, redis_client) -> None:
    """
    Full RAG ingestion pipeline for a single document.

    Steps:
      1. Download PDF from MinIO
      2. Extract text with pypdf
      3. Split into chunks
      4. Compute embeddings + insert into pgvector
      5. Publish status loopback
    """
    record_id = payload.get("record_id", "")
    s3_key = payload.get("s3_key", "")
    s3_bucket = payload.get("s3_bucket", settings.TRAINING_BUCKET_NAME)
    source_name = payload.get("original_name", s3_key.split("/")[-1])
    metadata = payload.get("metadata", {})

    logger.info("rag_pipeline_start", extra={"record_id": record_id, "s3_key": s3_key})

    try:
        # ── Step 1: Download from MinIO ──────────────────────────────
        from app.infrastructure.adapters.s3_downloader import S3Downloader

        downloader = S3Downloader()
        # Offload blocking I/O to thread pool
        loop = asyncio.get_event_loop()
        pdf_bytes = await loop.run_in_executor(
            None, downloader.download, s3_key, s3_bucket
        )
        logger.info("pdf_downloaded", extra={"s3_key": s3_key, "size": len(pdf_bytes)})

        # ── Step 2: Extract text from PDF ────────────────────────────
        text = _extract_text_from_pdf(pdf_bytes)
        if not text.strip():
            raise ValueError("PDF vacío o no contiene texto extraíble.")
        logger.info("pdf_text_extracted", extra={"chars": len(text), "s3_key": s3_key})

        # ── Step 3: Split into chunks ────────────────────────────────
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_text(text)
        logger.info("text_chunked", extra={"chunks": len(chunks), "s3_key": s3_key})

        if not chunks:
            raise ValueError("No se generaron chunks del texto extraído.")

        # ── Step 4: Embed + Insert into pgvector ─────────────────────
        from app.infrastructure.adapters.pgvector_store import PgVectorStore

        store = PgVectorStore()
        await store.initialize()

        # Delete existing chunks for this s3_key (handles re-uploads)
        deleted = await store.delete_by_s3_key(s3_key)
        if deleted:
            logger.info("old_chunks_deleted", extra={"s3_key": s3_key, "deleted": deleted})

        # Generate a doc_id for this ingestion
        doc_id = record_id or str(uuid.uuid4())

        inserted = await store.insert_chunks(
            doc_id=doc_id,
            s3_key=s3_key,
            source_name=source_name,
            chunks=chunks,
            metadata=metadata,
        )

        logger.info(
            "rag_pipeline_success",
            extra={
                "record_id": record_id,
                "doc_id": doc_id,
                "chunks_inserted": inserted,
                "s3_key": s3_key,
            },
        )

        # ── Step 5: Publish INDEXED status loopback ──────────────────
        await _publish_status(
            redis_client,
            record_id=record_id,
            status="INDEXED",
            extra={"chunks_count": inserted, "doc_id": doc_id},
        )

    except Exception as e:
        logger.error(
            "rag_pipeline_failed",
            extra={
                "record_id": record_id,
                "s3_key": s3_key,
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )
        # Publish FAILED status loopback
        await _publish_status(
            redis_client,
            record_id=record_id,
            status="FAILED",
            error_message=str(e),
        )


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from a PDF in memory using pypdf.

    Returns concatenated text from all pages.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


async def _publish_status(
    redis_client,
    record_id: str,
    status: str,
    error_message: str = "",
    extra: dict | None = None,
) -> None:
    """
    Publish a status update to Redis for Django to consume.

    Channel: mole:training:status
    Payload: {record_id, status, asset_type, error_message, ...extra}

    Django's Celery worker can subscribe to this channel and call
    `update_training_status` to update the DB record.
    """
    payload = {
        "event_type": "training.status_update",
        "record_id": record_id,
        "asset_type": "document",
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
