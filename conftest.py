# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
#
# AVISO DE PROPIEDAD INTELECTUAL:
# Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
# Queda estrictamente prohibida la copia, modificación, distribución,
# sublicenciamiento o uso comercial de este código, total o parcialmente,
# sin la autorización expresa y por escrito de los titulares del Copyright.
#
# Cualquier uso no autorizado será perseguido conforme a la Ley Federal
# del Derecho de Autor (México) y tratados internacionales aplicables.
# =============================================================================
"""
Root conftest for pytest.
Overrides Redis-dependent settings so tests run locally without Redis.
Creates unmanaged tables (managed=False) in the test database.
"""
import django
from django.conf import settings
import pytest


def pytest_configure(config):
    # Override CACHES to use in-memory backend (no Redis required)
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    # Override CHANNEL_LAYERS to use InMemoryChannelLayer
    settings.CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }


@pytest.fixture(autouse=True, scope="session")
def _create_unmanaged_tables(django_db_setup, django_db_blocker):
    """Create tables for unmanaged models so tests can use them."""
    with django_db_blocker.unblock():
        from django.db import connection
        with connection.schema_editor() as editor:
            from apps.plants.infrastructure.repositories.models import UserPlant
            from apps.core.infrastructure.repositories.models import SensorLog
            for model in (UserPlant, SensorLog):
                try:
                    editor.create_model(model)
                except Exception:
                    pass  # table may already exist
