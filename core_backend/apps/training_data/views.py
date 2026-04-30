# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
API Views for the Training Data Pipeline.

Endpoints:
  POST /api/v1/training/documents/upload/request/  → Presigned URL for PDF
  POST /api/v1/training/images/upload/request/      → Presigned URL for image/ZIP
  POST /api/v1/training/upload/confirm/             → Confirm upload completed
  GET  /api/v1/training/documents/                  → List training documents
  GET  /api/v1/training/images/                     → List training images

Upload Flow (Presigned URL):
  1. Frontend requests a presigned PUT URL from Django (Step 1)
  2. Frontend uploads file directly to MinIO/S3 (Step 2 — no Django proxy)
  3. Frontend confirms the upload to Django (Step 3 → triggers Celery)
"""
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.training_data.models import (
    ProcessingStatus,
    TrainingDocument,
    TrainingImage,
)
from apps.training_data.serializers import (
    DocumentUploadRequestSerializer,
    ImageUploadRequestSerializer,
    PresignedUrlResponseSerializer,
    TrainingDocumentSerializer,
    TrainingImageSerializer,
    UploadConfirmResponseSerializer,
    UploadConfirmSerializer,
)
from apps.training_data.services import S3TrainingService
from apps.training_data.tasks import notify_training_asset

logger = logging.getLogger(__name__)


# ── Presigned URL Request Endpoints ──────────────────────────────────────


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def document_upload_request_view(request):
    """
    Step 1: Generate a presigned PUT URL for uploading a training document.
    Creates a TrainingDocument record with status=PENDING.
    """
    serializer = DocumentUploadRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # Validate file size
    max_size = getattr(settings, 'TRAINING_MAX_PDF_SIZE', 50 * 1024 * 1024)
    if data['file_size'] > max_size:
        return Response(
            {'error': f'El archivo excede el límite de {max_size // (1024*1024)}MB.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        svc = S3TrainingService()
        s3_key = svc.generate_document_key(data['original_name'])
        ttl = getattr(settings, 'TRAINING_PRESIGNED_TTL', 900)

        presigned_url = svc.generate_presigned_put_url(
            s3_key=s3_key,
            content_type=data['content_type'],
            max_content_length=data['file_size'],
            ttl=ttl,
        )

        # Create DB record
        record = TrainingDocument.objects.create(
            uploaded_by=request.user,
            s3_key=s3_key,
            s3_bucket=getattr(settings, 'TRAINING_BUCKET_NAME', 'mole-training-data'),
            original_name=data['original_name'],
            content_type=data['content_type'],
            file_size=data['file_size'],
            category=data.get('category', 'other'),
            language=data.get('language', 'es'),
            description=data.get('description', ''),
            status=ProcessingStatus.PENDING,
        )

        response_data = {
            'presigned_url': presigned_url,
            's3_key': s3_key,
            'record_id': record.id,
            'expires_in': ttl,
            'content_type': data['content_type'],
        }
        return Response(
            PresignedUrlResponseSerializer(response_data).data,
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.exception("document_upload_request_failed")
        return Response(
            {'error': f'Error generando URL presignada: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def image_upload_request_view(request):
    """
    Step 1: Generate a presigned PUT URL for uploading a training image/ZIP.
    Creates a TrainingImage record with status=PENDING.
    """
    serializer = ImageUploadRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # Validate file size
    max_size = getattr(settings, 'TRAINING_MAX_IMAGE_SIZE', 200 * 1024 * 1024)
    if data['file_size'] > max_size:
        return Response(
            {'error': f'El archivo excede el límite de {max_size // (1024*1024)}MB.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        svc = S3TrainingService()
        s3_key = svc.generate_image_key(data['original_name'])
        ttl = getattr(settings, 'TRAINING_PRESIGNED_TTL', 900)

        presigned_url = svc.generate_presigned_put_url(
            s3_key=s3_key,
            content_type=data['content_type'],
            max_content_length=data['file_size'],
            ttl=ttl,
        )

        # Create DB record
        record = TrainingImage.objects.create(
            uploaded_by=request.user,
            s3_key=s3_key,
            s3_bucket=getattr(settings, 'TRAINING_BUCKET_NAME', 'mole-training-data'),
            original_name=data['original_name'],
            content_type=data['content_type'],
            file_size=data['file_size'],
            species_id=data.get('species_id'),
            disease_label=data.get('disease_label', ''),
            severity=data.get('severity', 'medium'),
            geo_location=data.get('geo_location', {}),
            description=data.get('description', ''),
            status=ProcessingStatus.PENDING,
        )

        response_data = {
            'presigned_url': presigned_url,
            's3_key': s3_key,
            'record_id': record.id,
            'expires_in': ttl,
            'content_type': data['content_type'],
        }
        return Response(
            PresignedUrlResponseSerializer(response_data).data,
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.exception("image_upload_request_failed")
        return Response(
            {'error': f'Error generando URL presignada: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ── Upload Confirmation Endpoint ─────────────────────────────────────────


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def upload_confirm_view(request):
    """
    Step 3: Frontend confirms that the presigned upload completed.
    Django verifies the object exists in S3 via HEAD, then enqueues Celery notification.
    """
    serializer = UploadConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    record_id = str(data['record_id'])
    asset_type = data['asset_type']

    try:
        # Fetch the record
        if asset_type == 'document':
            record = TrainingDocument.objects.get(pk=record_id)
        else:
            record = TrainingImage.objects.get(pk=record_id)

        # Guard: only PENDING records can be confirmed
        if record.status != ProcessingStatus.PENDING:
            return Response(
                {'error': f'El registro ya tiene estado: {record.status}'},
                status=status.HTTP_409_CONFLICT,
            )

        # Verify object exists in S3 (ensure bucket first)
        svc = S3TrainingService()
        svc.ensure_bucket_exists()
        obj_info = svc.verify_object_exists(record.s3_key)

        if not obj_info['exists']:
            record.status = ProcessingStatus.FAILED
            record.error_message = 'Objeto no encontrado en S3 tras confirmación de subida.'
            record.save(update_fields=['status', 'error_message', 'updated_at'])
            return Response(
                {'error': 'El archivo no fue encontrado en el almacenamiento.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Update record with verified S3 metadata
        record.status = ProcessingStatus.UPLOADED
        record.file_size = obj_info['size']
        record.save(update_fields=['status', 'file_size', 'updated_at'])

        # Enqueue Celery notification to microservice
        task = notify_training_asset.delay(record_id, asset_type)  # type: ignore
        record.celery_task_id = task.id
        record.save(update_fields=['celery_task_id'])

        response_data = {
            'record_id': record.id,
            'status': record.status,
            's3_verified': True,
            'file_size': obj_info['size'],
        }
        return Response(
            UploadConfirmResponseSerializer(response_data).data,
            status=status.HTTP_200_OK,
        )

    except (TrainingDocument.DoesNotExist, TrainingImage.DoesNotExist):
        return Response(
            {'error': 'Registro no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.exception("upload_confirm_failed")
        return Response(
            {'error': f'Error confirmando subida: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ── List Endpoints (Read-only) ───────────────────────────────────────────


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_training_documents_view(request):
    """List all training documents with optional status filter."""
    qs = TrainingDocument.objects.all()
    status_filter = request.query_params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)
    serializer = TrainingDocumentSerializer(qs[:100], many=True)
    return Response({'count': qs.count(), 'results': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_training_images_view(request):
    """List all training images with optional status/disease filter."""
    qs = TrainingImage.objects.all()
    status_filter = request.query_params.get('status')
    disease_filter = request.query_params.get('disease_label')
    if status_filter:
        qs = qs.filter(status=status_filter)
    if disease_filter:
        qs = qs.filter(disease_label__icontains=disease_filter)
    serializer = TrainingImageSerializer(qs[:100], many=True)
    return Response({'count': qs.count(), 'results': serializer.data})
