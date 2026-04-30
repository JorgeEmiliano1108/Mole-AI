# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
DRF Serializers for the Training Data Pipeline.

Two flows:
  1. Upload Request  — validates metadata, returns presigned URL
  2. Upload Confirm  — validates record_id, triggers Celery notification
"""
from rest_framework import serializers

from apps.training_data.models import (
    ProcessingStatus,
    TrainingDocument,
    TrainingImage,
)


# ── Upload Request Serializers ───────────────────────────────────────────


class DocumentUploadRequestSerializer(serializers.Serializer):
    """Input for requesting a presigned URL to upload a training PDF."""
    original_name = serializers.CharField(max_length=255)
    content_type = serializers.ChoiceField(
        choices=['application/pdf', 'text/plain'],
        default='application/pdf',
    )
    file_size = serializers.IntegerField(min_value=1)
    category = serializers.ChoiceField(
        choices=[c[0] for c in TrainingDocument.CATEGORY_CHOICES],
        default='other',
    )
    language = serializers.CharField(max_length=5, default='es')
    description = serializers.CharField(required=False, allow_blank=True, default='')


class ImageUploadRequestSerializer(serializers.Serializer):
    """Input for requesting a presigned URL to upload a training image/ZIP."""
    original_name = serializers.CharField(max_length=255)
    content_type = serializers.ChoiceField(
        choices=[
            'image/jpeg', 'image/png', 'image/webp',
            'application/zip', 'application/x-zip-compressed',
        ],
    )
    file_size = serializers.IntegerField(min_value=1)
    species_id = serializers.UUIDField(required=False, allow_null=True)
    disease_label = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    severity = serializers.ChoiceField(
        choices=[c[0] for c in TrainingImage.SEVERITY_CHOICES],
        default='medium',
    )
    geo_location = serializers.JSONField(required=False, default=dict)
    description = serializers.CharField(required=False, allow_blank=True, default='')


# ── Upload Confirm Serializer ────────────────────────────────────────────


class UploadConfirmSerializer(serializers.Serializer):
    """Input for confirming that a presigned upload completed."""
    record_id = serializers.UUIDField()
    asset_type = serializers.ChoiceField(choices=['document', 'image'])


# ── Response Serializers ─────────────────────────────────────────────────


class PresignedUrlResponseSerializer(serializers.Serializer):
    """Response after generating a presigned URL."""
    presigned_url = serializers.URLField()
    s3_key = serializers.CharField()
    record_id = serializers.UUIDField()
    expires_in = serializers.IntegerField()
    content_type = serializers.CharField()


class UploadConfirmResponseSerializer(serializers.Serializer):
    """Response after confirming an upload."""
    record_id = serializers.UUIDField()
    status = serializers.CharField()
    s3_verified = serializers.BooleanField()
    file_size = serializers.IntegerField()


# ── Model Serializers (Read) ────────────────────────────────────────────


class TrainingDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.EmailField(source='uploaded_by.email', read_only=True, default=None)

    class Meta:
        model = TrainingDocument
        fields = [
            'id', 'original_name', 's3_key', 'content_type', 'file_size',
            'category', 'language', 'description', 'status', 'error_message',
            'uploaded_by_email', 'created_at', 'processed_at',
        ]
        read_only_fields = fields


class TrainingImageSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.EmailField(source='uploaded_by.email', read_only=True, default=None)
    species_name = serializers.CharField(source='species.scientific_name', read_only=True, default=None)

    class Meta:
        model = TrainingImage
        fields = [
            'id', 'original_name', 's3_key', 'content_type', 'file_size',
            'species_name', 'disease_label', 'severity', 'geo_location',
            'description', 'status', 'error_message',
            'uploaded_by_email', 'created_at', 'processed_at',
        ]
        read_only_fields = fields
