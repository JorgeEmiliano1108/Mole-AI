# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Django ORM models for the MLOps Training Data Pipeline.

Two asset types stored in MinIO/S3 bucket `mole-training-data`:
  - TrainingDocument (prefix: documents/) → PDFs for RAG retraining (MS2)
  - TrainingImage    (prefix: images/)    → Labeled images for CNN fine-tuning (MS1)

LFPDPPP Compliance:
  - No PII stored in S3 keys (UUID-based naming)
  - User FK is SET_NULL on deletion to preserve audit trail
"""
import uuid

from django.conf import settings
from django.db import models


class AnonymizationStatus(models.TextChoices):
    """Estado de vida del registro anonimizado."""
    PENDING = 'PENDING', 'Pendiente'
    ANONYMIZED = 'ANONYMIZED', 'Anonimizado'
    EXCLUDED = 'EXCLUDED', 'Excluido por política'


class ProcessingStatus(models.TextChoices):
    """State machine for training asset lifecycle."""
    PENDING   = 'PENDING',   'Pendiente de subida'
    UPLOADING = 'UPLOADING', 'Subiendo a S3'
    UPLOADED  = 'UPLOADED',  'Almacenado en S3'
    INDEXING  = 'INDEXING',  'Procesando en microservicio'
    INDEXED   = 'INDEXED',   'Indexado / Procesado exitosamente'
    FAILED    = 'FAILED',    'Fallido'


class TrainingDocument(models.Model):
    """
    PDF/TXT documents for retraining the RAG knowledge base (MS2 - mole_chat).

    Lifecycle:
      PENDING → (presigned upload) → UPLOADED → (Celery notify) → INDEXING → INDEXED
                                                                            → FAILED
    """

    CATEGORY_CHOICES = [
        ('phytopathology', 'Fitopatología'),
        ('nutrition', 'Nutrición Vegetal'),
        ('agronomy', 'Agronomía General'),
        ('pest_control', 'Control de Plagas'),
        ('soil_science', 'Edafología'),
        ('regulations', 'Normatividad (NOM/SAGARPA)'),
        ('other', 'Otro'),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Ownership (LFPDPPP: SET_NULL preserves audit trail without retaining PII)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_documents',
    )

    # S3 Object metadata
    s3_key = models.CharField(
        max_length=512, unique=True, db_index=True,
        help_text='Full S3 key including prefix, e.g. documents/<uuid>.pdf',
    )
    s3_bucket = models.CharField(max_length=128, default='mole-training-data')
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, default='application/pdf')
    file_size = models.PositiveBigIntegerField(
        help_text='File size in bytes',
    )
    checksum_sha256 = models.CharField(
        max_length=64, blank=True,
        help_text='SHA-256 hex digest for integrity verification',
    )

    # Classification
    category = models.CharField(
        max_length=30, choices=CATEGORY_CHOICES, default='other',
    )
    language = models.CharField(max_length=5, default='es')
    description = models.TextField(
        blank=True,
        help_text='Brief description of document contents for catalog purposes',
    )

    # Pipeline state
    status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'training_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['category', 'status']),
        ]
        verbose_name = 'Training Document'
        verbose_name_plural = 'Training Documents'

    def __str__(self):
        return f"[{self.status}] {self.original_name} ({self.category})"


class TrainingImage(models.Model):
    """
    Labeled images / image ZIPs for CNN fine-tuning (MS1 - mole_vision).

    Lifecycle:
      PENDING → (presigned upload) → UPLOADED → (Celery notify) → INDEXING → INDEXED
                                                                            → FAILED
    """

    SEVERITY_CHOICES = [
        ('healthy', 'Sana'),
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Ownership
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_images',
    )

    # S3 Object metadata
    s3_key = models.CharField(
        max_length=512, unique=True, db_index=True,
        help_text='Full S3 key including prefix, e.g. images/<uuid>.zip',
    )
    s3_bucket = models.CharField(max_length=128, default='mole-training-data')
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, default='image/jpeg')
    file_size = models.PositiveBigIntegerField(
        help_text='File size in bytes',
    )
    checksum_sha256 = models.CharField(
        max_length=64, blank=True,
        help_text='SHA-256 hex digest for integrity verification',
    )

    # Agronomic labeling
    species = models.ForeignKey(
        'plants.SpeciesCatalog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_images',
        help_text='Plant species depicted in the image',
    )
    disease_label = models.CharField(
        max_length=100, blank=True,
        help_text='Disease or condition label, e.g. "roya", "tizón tardío"',
    )
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, default='medium',
    )
    geo_location = models.JSONField(
        default=dict, blank=True,
        help_text='Capture coordinates: {"lat": float, "lon": float}',
    )
    description = models.TextField(
        blank=True,
        help_text='Additional notes about the image or dataset',
    )

    # Pipeline state
    status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'training_images'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['species', 'disease_label']),
            models.Index(fields=['status', 'created_at']),
        ]
        verbose_name = 'Training Image'
        verbose_name_plural = 'Training Images'

    def __str__(self):
        label = self.disease_label or 'unlabeled'
        return f"[{self.status}] {self.original_name} ({label})"


class TrainingDatasetAnon(models.Model):
    """Tabla espejo de entrenamiento sin PII (Track B - Anonimización).

    Derivada del payload de diagnóstico (AIDiagnostic). Se omite:
      - user FK
      - image_path (ruta potencialmente identificable)
      - cualquier otro campo sensible.

    El `subject_hash` permite agrupar registros del mismo sujeto (planta +
    contexto) sin revelar identidad, usando HMAC-SHA256 con clave inyectada por
    variable de entorno (`ANONIMIZACION_KEY`).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record_type = models.CharField(
        max_length=50,
        default='diagnostic',
        db_index=True,
        help_text='Tipo de registro de entrenamiento, e.g. diagnostic, sensor.',
    )
    source_fingerprint = models.CharField(
        max_length=128,
        blank=True,
        db_index=True,
        help_text='HMAC-SHA256 del ID de fuente (no reversible).',
    )
    subject_hash = models.CharField(
        max_length=128,
        db_index=True,
        help_text='HMAC-SHA256 del par usuario+planta para agrupar series temporales.',
    )
    feature_payload = models.JSONField(
        default=dict,
        help_text='Datos de entrenamiento sin PII (diagnóstico, confianza, metadatos).',
    )
    label = models.TextField(
        blank=True,
        help_text='Etiqueta supervisada para entrenamiento (e.g. diagnosis_label).',
    )
    status = models.CharField(
        max_length=20,
        choices=AnonymizationStatus.choices,
        default=AnonymizationStatus.ANONYMIZED,
        db_index=True,
    )
    purged = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True si el registro se exportó durante el ejercicio del derecho de cancelación (ARCO).",
    )
    anonymized_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'training_dataset_anon'
        ordering = ['-anonymized_at']
        indexes = [
            models.Index(fields=['record_type', 'subject_hash']),
            models.Index(fields=['status', 'anonymized_at']),
        ]
        verbose_name = 'Training Dataset Anonymized Record'
        verbose_name_plural = 'Training Dataset Anonymized Records'

    def __str__(self):
        return f"[{self.record_type}] {self.subject_hash[:16]}... @ {self.anonymized_at}"
