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
from django.apps import AppConfig
from django.core.checks import Error, register


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'


@register()
def check_embedding_dimension(app_configs, **kwargs):
    """P0: la DDL de BotanicalKnowledge debe coincidir con el modelo NIM.

    Si difieren, pgvector falla en INSERT/`<=>` en tiempo de ejecución.
    """
    from django.conf import settings
    from apps.core.models import BotanicalKnowledge

    errors = []
    field_dim = BotanicalKnowledge._meta.get_field('embedding').dimensions
    expected = getattr(settings, 'LLM_EMBEDDING_DIMENSION', 1024)
    if field_dim != expected:
        errors.append(
            Error(
                f"BotanicalKnowledge.embedding es vector({field_dim}) pero "
                f"LLM_EMBEDDING_DIMENSION={expected}. Alinea el modelo o la DDL.",
                id='mole_ai.E001',
            )
        )
    return errors
