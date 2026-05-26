# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
from django.urls import path

from apps.training_data import views

app_name = 'training_data'

urlpatterns = [
    # Step 1: Request presigned upload URL
    path(
        'documents/upload/request/',
        views.document_upload_request_view,
        name='document_upload_request',
    ),
    path(
        'images/upload/request/',
        views.image_upload_request_view,
        name='image_upload_request',
    ),

    # Step 3: Confirm upload completed (triggers Celery → Redis notification)
    path(
        'upload/confirm/',
        views.upload_confirm_view,
        name='upload_confirm',
    ),

    # Read-only list endpoints
    path(
        'documents/',
        views.list_training_documents_view,
        name='list_documents',
    ),
    path(
        'images/',
        views.list_training_images_view,
        name='list_images',
    ),
]
