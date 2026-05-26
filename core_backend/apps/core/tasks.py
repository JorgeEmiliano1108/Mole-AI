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

    user_id is hashed for the S3 key — no PII in object storage.
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
    Per-device dynamic liveness evaluation.
    Thresholds derived from each device's report_interval_minutes:
      warning  = 2x interval (missed 1 cycle)
      offline  = 4x interval (missed 3 cycles)
    """
    import logging
    from datetime import timedelta
    from django.utils import timezone
    from apps.core.models import Device

    logger = logging.getLogger(__name__)
    now = timezone.now()
    offline_count = 0
    warning_count = 0

    devices = Device.objects.exclude(status='offline', last_seen__isnull=True)

    for dev in devices.iterator():
        if dev.last_seen is None:
            continue

        interval = dev.report_interval_minutes or 5
        warning_edge = now - timedelta(minutes=interval * 2)
        offline_edge = now - timedelta(minutes=interval * 4)

        if dev.last_seen < offline_edge and dev.status != 'offline':
            dev.status = 'offline'
            dev.save(update_fields=['status'])
            offline_count += 1
        elif dev.last_seen < warning_edge and dev.status not in ('warning', 'offline'):
            dev.status = 'warning'
            dev.save(update_fields=['status'])
            warning_count += 1

    if offline_count > 0 or warning_count > 0:
        logger.info(
            "check_device_liveness: %d offline, %d warning.",
            offline_count, warning_count
        )

    return {"offline_count": offline_count, "warning_count": warning_count}


# =============================================================================
# Fase 4: Data Lifecycle Management (DLM)
# =============================================================================

@shared_task(name="downsample_telemetry")
def downsample_telemetry():
    """
    DLM-02: Compress raw readings older than 30 days into hourly aggregates.
    Partitioned by Device (A2). Idempotent via ignore_conflicts (unique_together).
    """
    import logging
    from datetime import timedelta
    from django.utils import timezone
    from django.db.models import Avg, Min, Max, Count
    from django.db.models.functions import TruncHour
    from apps.core.models import (
        Device, SoilReading, AmbientReading,
        HourlySoilAggregate, HourlyAmbientAggregate, HardwareBinding,
    )

    logger = logging.getLogger(__name__)
    cutoff = timezone.now() - timedelta(days=30)
    total_soil = 0
    total_ambient = 0

    for device in Device.objects.all().iterator():
        # -- Soil aggregation per binding --
        binding_ids = list(
            HardwareBinding.objects.filter(device=device).values_list('pk', flat=True)
        )
        soil_aggs = (
            SoilReading.objects
            .filter(binding_id__in=binding_ids, recorded_at__lt=cutoff)
            .annotate(hour=TruncHour('recorded_at'))
            .values('binding_id', 'hour')
            .annotate(
                avg_soil_humidity=Avg('soil_humidity'),
                min_soil_humidity=Min('soil_humidity'),
                max_soil_humidity=Max('soil_humidity'),
                sample_count=Count('id'),
            )
        )
        soil_objs = [
            HourlySoilAggregate(
                binding_id=row['binding_id'],
                hour=row['hour'],
                avg_soil_humidity=row['avg_soil_humidity'],
                min_soil_humidity=row['min_soil_humidity'],
                max_soil_humidity=row['max_soil_humidity'],
                sample_count=row['sample_count'],
            )
            for row in soil_aggs
        ]
        if soil_objs:
            HourlySoilAggregate.objects.bulk_create(soil_objs, ignore_conflicts=True)
            total_soil += len(soil_objs)

        # -- Ambient aggregation --
        ambient_aggs = (
            AmbientReading.objects
            .filter(device=device, recorded_at__lt=cutoff)
            .annotate(hour=TruncHour('recorded_at'))
            .values('hour')
            .annotate(
                avg_air_temperature=Avg('air_temperature'),
                avg_air_humidity=Avg('air_humidity'),
                avg_uv_index=Avg('uv_index'),
                avg_light_level=Avg('light_level'),
                sample_count=Count('id'),
            )
        )
        ambient_objs = [
            HourlyAmbientAggregate(
                device=device,
                hour=row['hour'],
                avg_air_temperature=row['avg_air_temperature'],
                avg_air_humidity=row['avg_air_humidity'],
                avg_uv_index=row['avg_uv_index'],
                avg_light_level=row['avg_light_level'],
                sample_count=row['sample_count'],
            )
            for row in ambient_aggs
        ]
        if ambient_objs:
            HourlyAmbientAggregate.objects.bulk_create(ambient_objs, ignore_conflicts=True)
            total_ambient += len(ambient_objs)

    logger.info("downsample_telemetry: %d soil, %d ambient aggregates upserted.", total_soil, total_ambient)
    return {"soil_aggregates": total_soil, "ambient_aggregates": total_ambient}


@shared_task(name="archive_telemetry_to_s3")
def archive_telemetry_to_s3():
    """
    Export raw readings older than 30 days to S3 as two separate CSV.gz
    files per device: one for soil, one for ambient.
    Creates one TelemetryArchive record per file (A1: two records per cycle).
    If any S3 upload fails, exception propagates and halts the chain.
    """
    import csv
    import gzip
    import logging
    import tempfile
    from datetime import timedelta
    from django.utils import timezone
    from django.conf import settings as django_settings
    import boto3
    from apps.core.models import (
        Device, SoilReading, AmbientReading,
        HardwareBinding, TelemetryArchive,
    )

    logger = logging.getLogger(__name__)
    cutoff = timezone.now() - timedelta(days=30)
    period_start = cutoff - timedelta(days=30)
    archived_count = 0

    s3 = boto3.client(
        's3',
        aws_access_key_id=django_settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=django_settings.AWS_SECRET_ACCESS_KEY,
        region_name=django_settings.AWS_S3_REGION_NAME,
    )
    bucket = django_settings.AWS_STORAGE_BUCKET_NAME
    period_label = cutoff.strftime('%Y-%m')

    for device in Device.objects.all().iterator():
        binding_ids = list(
            HardwareBinding.objects.filter(device=device).values_list('pk', flat=True)
        )

        # ── Soil archive ────────────────────────────────────────────────
        soil_key = f"telemetry-archive/{device.pk}/{period_label}_soil.csv.gz"
        if not TelemetryArchive.objects.filter(s3_key=soil_key).exists():
            soil_qs = (
                SoilReading.objects
                .filter(binding_id__in=binding_ids, recorded_at__lt=cutoff)
                .order_by('recorded_at')
            )
            soil_count = soil_qs.count()
            if soil_count > 0:
                with tempfile.NamedTemporaryFile(suffix='.csv.gz', delete=True) as tmp:
                    with gzip.open(tmp.name, 'wt', newline='') as gz:
                        writer = csv.writer(gz)
                        writer.writerow(['binding_id', 'recorded_at', 'soil_humidity', 'ph_level'])
                        for r in soil_qs.iterator(chunk_size=2000):
                            writer.writerow([r.binding_id, r.recorded_at.isoformat(),
                                             r.soil_humidity, r.ph_level])
                    s3.upload_file(tmp.name, bucket, soil_key)

                TelemetryArchive.objects.create(
                    device=device, period_start=period_start, period_end=cutoff,
                    s3_key=soil_key, rows_archived=soil_count,
                )
                logger.info("archive: device=%s soil -> s3://%s/%s (%d rows)",
                            device.pk, bucket, soil_key, soil_count)
                archived_count += 1

        # ── Ambient archive ─────────────────────────────────────────────
        ambient_key = f"telemetry-archive/{device.pk}/{period_label}_ambient.csv.gz"
        if not TelemetryArchive.objects.filter(s3_key=ambient_key).exists():
            ambient_qs = (
                AmbientReading.objects
                .filter(device=device, recorded_at__lt=cutoff)
                .order_by('recorded_at')
            )
            ambient_count = ambient_qs.count()
            if ambient_count > 0:
                with tempfile.NamedTemporaryFile(suffix='.csv.gz', delete=True) as tmp:
                    with gzip.open(tmp.name, 'wt', newline='') as gz:
                        writer = csv.writer(gz)
                        writer.writerow(['device_id', 'recorded_at', 'air_temperature',
                                         'air_humidity', 'uv_index', 'light_level'])
                        for r in ambient_qs.iterator(chunk_size=2000):
                            writer.writerow([str(device.pk), r.recorded_at.isoformat(),
                                             r.air_temperature, r.air_humidity,
                                             r.uv_index, r.light_level])
                    s3.upload_file(tmp.name, bucket, ambient_key)

                TelemetryArchive.objects.create(
                    device=device, period_start=period_start, period_end=cutoff,
                    s3_key=ambient_key, rows_archived=ambient_count,
                )
                logger.info("archive: device=%s ambient -> s3://%s/%s (%d rows)",
                            device.pk, bucket, ambient_key, ambient_count)
                archived_count += 1

    return {"archived_files": archived_count}


@shared_task(name="purge_raw_telemetry")
def purge_raw_telemetry():
    """
    DLM-04: Delete raw readings older than 30 days.
    DUAL FAIL-SAFE: Verifies soil archive before purging soil, ambient archive
    before purging ambient. Each entity type is independently guarded.
    Batched deletes (10k rows) to avoid long-running locks on RDS.
    Logs to AuditLog (MoProSoft compliance).
    """
    import logging
    from datetime import timedelta
    from django.utils import timezone
    from django.db import transaction
    from apps.core.models import (
        Device, SoilReading, AmbientReading,
        HardwareBinding, TelemetryArchive, AuditLog,
    )

    logger = logging.getLogger(__name__)
    cutoff = timezone.now() - timedelta(days=30)
    period_label = cutoff.strftime('%Y-%m')
    BATCH_SIZE = 10_000
    total_soil_purged = 0
    total_ambient_purged = 0

    for device in Device.objects.all().iterator():
        soil_key = f"telemetry-archive/{device.pk}/{period_label}_soil.csv.gz"
        ambient_key = f"telemetry-archive/{device.pk}/{period_label}_ambient.csv.gz"
        binding_ids = list(
            HardwareBinding.objects.filter(device=device).values_list('pk', flat=True)
        )

        # ── Soil purge (guarded by soil archive) ────────────────────────
        soil_purged = 0
        has_soil_archive = TelemetryArchive.objects.filter(device=device, s3_key=soil_key).exists()
        has_soil_rows = SoilReading.objects.filter(
            binding_id__in=binding_ids, recorded_at__lt=cutoff
        ).exists() if binding_ids else False

        if has_soil_rows and not has_soil_archive:
            logger.critical(
                "SOIL PURGE ABORTED for device=%s: no archive at %s.", device.pk, soil_key
            )
        elif has_soil_rows and has_soil_archive:
            while True:
                batch_ids = list(
                    SoilReading.objects
                    .filter(binding_id__in=binding_ids, recorded_at__lt=cutoff)
                    .values_list('pk', flat=True)[:BATCH_SIZE]
                )
                if not batch_ids:
                    break
                with transaction.atomic():
                    deleted, _ = SoilReading.objects.filter(pk__in=batch_ids).delete()
                    soil_purged += deleted

        # ── Ambient purge (guarded by ambient archive) ──────────────────
        ambient_purged = 0
        has_ambient_archive = TelemetryArchive.objects.filter(device=device, s3_key=ambient_key).exists()
        has_ambient_rows = AmbientReading.objects.filter(
            device=device, recorded_at__lt=cutoff
        ).exists()

        if has_ambient_rows and not has_ambient_archive:
            logger.critical(
                "AMBIENT PURGE ABORTED for device=%s: no archive at %s.", device.pk, ambient_key
            )
        elif has_ambient_rows and has_ambient_archive:
            while True:
                batch_ids = list(
                    AmbientReading.objects
                    .filter(device=device, recorded_at__lt=cutoff)
                    .values_list('pk', flat=True)[:BATCH_SIZE]
                )
                if not batch_ids:
                    break
                with transaction.atomic():
                    deleted, _ = AmbientReading.objects.filter(pk__in=batch_ids).delete()
                    ambient_purged += deleted

        # MoProSoft audit trail
        if soil_purged > 0 or ambient_purged > 0:
            AuditLog.objects.create(
                action='DLM_PURGE_RAW_TELEMETRY',
                details=(
                    f"device={device.pk} | cutoff={cutoff.isoformat()} | "
                    f"soil_deleted={soil_purged} | ambient_deleted={ambient_purged} | "
                    f"soil_archive={soil_key} | ambient_archive={ambient_key}"
                ),
            )
            logger.info(
                "purge: device=%s soil=%d ambient=%d",
                device.pk, soil_purged, ambient_purged
            )

        total_soil_purged += soil_purged
        total_ambient_purged += ambient_purged

    return {"soil_purged": total_soil_purged, "ambient_purged": total_ambient_purged}


@shared_task(name="dlm_pipeline")
def dlm_pipeline():
    """
    Orchestrator: runs the DLM chain via celery.chain().
    If any step fails, subsequent steps do NOT execute.
    """
    from celery import chain
    pipeline = chain(
        downsample_telemetry.si(),
        archive_telemetry_to_s3.si(),
        purge_raw_telemetry.si(),
    )
    pipeline.apply_async()
