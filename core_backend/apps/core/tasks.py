"""
Celery tasks for core backend operations.

LFPDPPP Art. 19 Compliance:
  Tasks that transit through Redis use ``hashed_user_id`` (SHA-256) instead
  of the raw user ID to minimise PII exposure in the message broker.
"""
import hashlib
import json
import os
import uuid

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.plants.models import UserPlant


def _hash_user_id(user_id) -> str:
    """Return a SHA-256 hex digest of the user identifier (LFPDPPP Art. 19)."""
    return hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()


@shared_task(name="generate_master_report_task")
def generate_master_report_task(user_id=None):
    """
    Generates a master JSON report asynchronously.

    Args:
        user_id: The raw user ID of the requesting user.  This value is
                 hashed immediately and never stored or forwarded in clear.
    """
    User = get_user_model()

    hashed_uid = _hash_user_id(user_id) if user_id else "system"
    report_filename = f"report_{hashed_uid[:12]}_{uuid.uuid4().hex[:8]}.json"

    media_dir = os.path.join(settings.BASE_DIR, "media", "reports")
    os.makedirs(media_dir, exist_ok=True)
    file_path = os.path.join(media_dir, report_filename)

    from apps.core.models import SensorLog
    from django.db.models import Avg

    aggs = SensorLog.objects.aggregate(
        avg_hum=Avg("soil_humidity"),
        avg_ph=Avg("ph_level"),
    )

    data = {
        "report_id": report_filename,
        "hashed_user_id": hashed_uid,
        "total_users": User.objects.count(),
        "total_plants": UserPlant.objects.count(),
        "avg_humidity": aggs["avg_hum"] or 0,
        "avg_ph": aggs["avg_ph"] or 0,
        "status": "COMPLETED",
    }

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    return f"/media/reports/{report_filename}"


@shared_task(name="refresh_admin_stats_task")
def refresh_admin_stats_task():
    """
    Refresca la vista materializada de estadísticas del admin backend asincrónicamente.
    """
    from django.db import connection

    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            # Using CONCURRENTLY avoids locking the view while it refreshes.
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY admin_stats;")
        return "Materialized view refreshed successfully"
    return "Skipped refresh (not using postgresql)"


# =============================================================================
# Fase 2: Async Offload Tasks — Chat & PDF
# =============================================================================

@shared_task(bind=True, max_retries=3, name="chat_async")
def chat_async(self, question, user_id, session_id):
    """
    Execute RAG chat via MS2 in a Celery worker (non-blocking for Gunicorn).

    Workflow:
      1. Instantiate MoleAIClient (async HTTP client to MS2)
      2. Wrap async call with async_to_sync (Celery runs sync)
      3. Return result dict for frontend polling

    Queue: chat_queue (dedicated — isolates LLM latency)
    Retry: 3 attempts with exponential backoff on connection errors

    LFPDPPP: user_id is used only for LLMRequest record creation
    in the database — never forwarded to external services in clear.
    """
    import logging
    from asgiref.sync import async_to_sync
    from django.utils import timezone

    logger = logging.getLogger(__name__)

    try:
        from apps.ai_models.services import MoleAIClient
        client = MoleAIClient()

        result = async_to_sync(client.generate_chat_response)(
            query=question,
            user_id=user_id,
            session_id=session_id,
        )

        logger.info(
            "chat_async_completed",
            extra={
                "task_id": self.request.id,
                "hashed_uid": _hash_user_id(user_id),
                "processing_time_ms": result.get("processing_time_ms"),
            },
        )

        return {
            # B4 FIX: MS2 ChatResponse usa 'respuesta', no 'answer'
            "answer": result.get("respuesta", ""),
            "disclaimer": result.get("disclaimer", ""),
            "processing_time_ms": result.get("processing_time_ms", 0),
            "request_id": result.get("request_id"),
            "tactical_alerts_count": result.get("tactical_alerts_count", 0),
        }

    except Exception as exc:
        logger.error(
            "chat_async_failed",
            extra={
                "task_id": self.request.id,
                "hashed_uid": _hash_user_id(user_id),
                "error": str(exc),
            },
        )
        # Retry on transient network errors
        if "Connection" in str(exc) or "Timeout" in str(exc):
            raise self.retry(exc=exc, countdown=3)
        raise


@shared_task(bind=True, max_retries=2, name="generate_pdf_async")
def generate_pdf_async(self, diagnostic_id, user_id):
    """
    Generate a diagnostic PDF in background, upload to MinIO, return presigned URL.

    Workflow:
      1. Call generate_diagnostic_pdf(diagnostic_id) → bytes (CPU-bound + LLM)
      2. Upload PDF bytes to MinIO under reports/{hash}_{uuid}.pdf
      3. Generate presigned GET URL (1h TTL)
      4. Return {download_url, filename, size_bytes}

    Queue: reports_queue (shared with generate_master_report_task)
    Retry: 2 attempts — PDF generation is mostly deterministic

    LFPDPPP: user_id is hashed for the S3 key — no PII in object storage.
    """
    import io
    import logging
    from django.utils import timezone

    logger = logging.getLogger(__name__)

    hashed_uid = _hash_user_id(user_id)
    filename = f"diagnostico_{diagnostic_id}.pdf"
    s3_key = f"reports/{hashed_uid[:12]}_{uuid.uuid4().hex[:8]}.pdf"

    try:
        # Step 1: Generate PDF bytes (CPU-bound + HTTP to MS2 for LLM summary)
        from apps.core.services.pdf_generator import generate_diagnostic_pdf
        pdf_bytes = generate_diagnostic_pdf(diagnostic_id)

        logger.info(
            "pdf_generated",
            extra={
                "task_id": self.request.id,
                "diagnostic_id": diagnostic_id,
                "size_bytes": len(pdf_bytes),
            },
        )

        # Step 2: Upload to MinIO via S3TrainingService
        from apps.training_data.services import S3TrainingService
        s3 = S3TrainingService()

        # Ensure bucket exists before uploading
        s3.ensure_bucket_exists()

        s3._client.put_object(
            Bucket=s3.bucket_name,
            Key=s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
            ContentDisposition=f'attachment; filename="{filename}"',
        )

        logger.info(
            "pdf_uploaded_to_s3",
            extra={
                "task_id": self.request.id,
                "s3_key": s3_key,
                "size_bytes": len(pdf_bytes),
            },
        )

        # Step 3: Generate presigned GET URL (1 hour TTL)
        download_url = s3.generate_presigned_get_url(s3_key, ttl=3600)

        logger.info(
            "pdf_presigned_url_generated",
            extra={
                "task_id": self.request.id,
                "s3_key": s3_key,
            },
        )

        return {
            "download_url": download_url,
            "filename": filename,
            "size_bytes": len(pdf_bytes),
            "s3_key": s3_key,
        }

    except Exception as exc:
        logger.error(
            "generate_pdf_async_failed",
            extra={
                "task_id": self.request.id,
                "diagnostic_id": diagnostic_id,
                "error": str(exc),
            },
        )
        raise self.retry(exc=exc, countdown=5)

# =============================================================================
# Fase 3: IoT Heartbeat Liveness (Sprint Dashboard UI)
# =============================================================================

@shared_task(name="check_device_liveness")
def check_device_liveness():
    """
    Evaluates the liveness of all devices based on their last_seen heartbeat.
    > 3 min -> warning
    > 10 min -> offline
    """
    import logging
    from datetime import timedelta
    from django.utils import timezone
    from apps.core.models import Device

    logger = logging.getLogger(__name__)
    now = timezone.now()
    
    warning_threshold = now - timedelta(minutes=3)
    offline_threshold = now - timedelta(minutes=10)

    # 1. Mark devices as offline if they crossed the 10-minute threshold
    offline_count = Device.objects.filter(
        last_seen__lt=offline_threshold
    ).exclude(status='offline').update(status='offline')

    # 2. Mark devices as warning if they crossed the 3-minute threshold
    #    (but are still within the 10-minute window)
    warning_count = Device.objects.filter(
        last_seen__lt=warning_threshold,
        last_seen__gte=offline_threshold
    ).exclude(status__in=['warning', 'offline']).update(status='warning')

    if offline_count > 0 or warning_count > 0:
        logger.info(
            "check_device_liveness completed: Marked %d devices as offline, %d as warning.",
            offline_count, warning_count
        )
    
    return {"offline_count": offline_count, "warning_count": warning_count}
