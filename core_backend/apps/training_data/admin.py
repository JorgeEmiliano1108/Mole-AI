# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
from django.contrib import admin

from apps.training_data.models import TrainingDocument, TrainingImage


@admin.register(TrainingDocument)
class TrainingDocumentAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'category', 'status', 'file_size', 'uploaded_by', 'created_at']
    list_filter = ['status', 'category', 'language']
    search_fields = ['original_name', 's3_key']
    readonly_fields = ['id', 's3_key', 's3_bucket', 'checksum_sha256', 'celery_task_id', 'created_at', 'updated_at', 'processed_at']
    ordering = ['-created_at']


@admin.register(TrainingImage)
class TrainingImageAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'disease_label', 'severity', 'status', 'file_size', 'uploaded_by', 'created_at']
    list_filter = ['status', 'severity', 'disease_label']
    search_fields = ['original_name', 's3_key', 'disease_label']
    readonly_fields = ['id', 's3_key', 's3_bucket', 'checksum_sha256', 'celery_task_id', 'created_at', 'updated_at', 'processed_at']
    ordering = ['-created_at']
