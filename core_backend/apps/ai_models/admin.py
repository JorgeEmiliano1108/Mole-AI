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

# Register your models here.
from django.contrib import admin

from apps.ai_models.models import LLMRequest


@admin.register(LLMRequest)
class LLMRequestAdmin(admin.ModelAdmin):
    """Logs del agente RAG: lectura para Botánico, total para SuperAdmin."""

    list_display = ('user', 'session_id', 'request_type', 'status', 'created_at')
    list_filter = ('status', 'request_type', 'created_at')
    search_fields = ('user__username', 'prompt')
    readonly_fields = ('user', 'created_at')

    def has_add_permission(self, request):
        return False
