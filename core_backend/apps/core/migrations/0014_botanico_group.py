# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""Migración 0014: grupo Botánico (RBAC administrativo V2, web retirada).

Crea el grupo 'Botánico' con permisos solo-view sobre diagnósticos,
telemetría IoT y logs RAG. Idempotente (get_or_create en todo).
"""
from django.db import migrations


def create_botanico_group(apps, schema_editor):
    from apps.core.services.rbac import ensure_botanico_group
    ensure_botanico_group()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_device_owner'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_botanico_group, noop),
    ]
