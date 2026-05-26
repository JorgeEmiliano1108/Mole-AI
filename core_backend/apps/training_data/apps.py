# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
from django.apps import AppConfig


class TrainingDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.training_data'
    verbose_name = 'Training Data (MLOps Pipeline)'

    def ready(self):
        # Ensure Celery tasks are discovered
        import apps.training_data.tasks  # noqa: F401
