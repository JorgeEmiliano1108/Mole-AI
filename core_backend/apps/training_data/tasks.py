# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Celery tasks for the Training Data MLOps Pipeline.

LFPDPPP Art. 19 Compliance:
  Payloads published to Redis contain only s3_key and metadata.
  No PII (email, user_id) transits through the message broker.
"""
import json
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, name="notify_training_asset")
def notify_training_asset(self, record_id: str, asset_type: str):
    """
    Publish an event to Redis so the target microservice downloads the new asset.

    Channel: mole:training:new_asset
    Payload: {asset_type, s3_key, s3_bucket, content_type, metadata}

    Args:
        record_id: UUID of the TrainingDocument or TrainingImage.
        asset_type: 'document' (MS2/RAG) or 'image' (MS1/CNN).
    """
    import redis as redis_lib
    from django.conf import settings

    try:
        # Fetch the record
        if asset_type == 'document':
            from apps.training_data.models import TrainingDocument, ProcessingStatus
            record = TrainingDocument.objects.get(pk=record_id)
        elif asset_type == 'image':
            from apps.training_data.models import TrainingImage, ProcessingStatus
            record = TrainingImage.objects.get(pk=record_id)
        else:
            raise ValueError(f"Unknown asset_type: {asset_type}")

        # Build LFPDPPP-safe payload (no PII)
        payload = {
            'event_type': 'training.new_asset',
            'asset_type': asset_type,
            'record_id': str(record.id),
            's3_key': record.s3_key,
            's3_bucket': record.s3_bucket,
            'content_type': record.content_type,
            'file_size': record.file_size,
            'original_name': record.original_name,
        }

        # Add type-specific metadata
        if asset_type == 'document':
            payload['metadata'] = {
                'category': record.category,
                'language': record.language,
            }
        elif asset_type == 'image':
            payload['metadata'] = {
                'disease_label': record.disease_label,
                'severity': record.severity,
                'species_id': str(record.species_id) if record.species_id else None,
            }

        # Publish to Redis
        redis_url = getattr(settings, 'REDIS_URL', 'redis://redis:6379/1')
        r = redis_lib.from_url(redis_url)
        channel = 'mole:training:new_asset'
        r.publish(channel, json.dumps(payload))

        # Update record status
        record.status = ProcessingStatus.INDEXING
        record.celery_task_id = self.request.id or ''
        record.save(update_fields=['status', 'celery_task_id', 'updated_at'])

        logger.info(
            "training_asset_notified",
            extra={
                'channel': channel,
                'asset_type': asset_type,
                'record_id': record_id,
                's3_key': record.s3_key,
            },
        )
        return {'status': 'notified', 'record_id': record_id, 'channel': channel}

    except Exception as exc:
        logger.error(
            "training_asset_notification_failed",
            extra={'record_id': record_id, 'error': str(exc)},
        )
        raise self.retry(exc=exc, countdown=5)


@shared_task(bind=True, max_retries=3, name="update_training_status")
def update_training_status(self, record_id: str, asset_type: str, new_status: str, error_message: str = ''):
    """
    Update the processing status of a training record.

    Called by microservices (via Redis subscriber → Celery) after processing:
      - INDEXED: asset successfully processed
      - FAILED:  processing error (with error_message)
    """
    try:
        from apps.training_data.models import ProcessingStatus

        if asset_type == 'document':
            from apps.training_data.models import TrainingDocument
            record = TrainingDocument.objects.get(pk=record_id)
        elif asset_type == 'image':
            from apps.training_data.models import TrainingImage
            record = TrainingImage.objects.get(pk=record_id)
        else:
            raise ValueError(f"Unknown asset_type: {asset_type}")

        # Validate status transition
        valid_statuses = {s.value for s in ProcessingStatus}
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        record.status = new_status
        record.error_message = error_message
        if new_status in (ProcessingStatus.INDEXED, ProcessingStatus.FAILED):
            record.processed_at = timezone.now()
        record.save(update_fields=['status', 'error_message', 'processed_at', 'updated_at'])

        logger.info(
            "training_status_updated",
            extra={'record_id': record_id, 'new_status': new_status},
        )
        return {'status': 'updated', 'record_id': record_id, 'new_status': new_status}

    except Exception as exc:
        logger.error(
            "training_status_update_failed",
            extra={'record_id': record_id, 'error': str(exc)},
        )
        raise self.retry(exc=exc, countdown=5)
