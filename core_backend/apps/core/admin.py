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
from django.contrib import admin

from apps.core.models import (
    AIDiagnostic,
    AmbientReading,
    AuditLog,
    Device,
    FeedbackTicket,
    SensorLog,
    SoilReading,
)


@admin.register(FeedbackTicket)
class FeedbackTicketAdmin(admin.ModelAdmin):
    list_display = ('topic', 'user', 'status', 'created_at')
    list_filter = ('status', 'topic')
    search_fields = ('message', 'user__username', 'user__email')
    readonly_fields = ('user', 'created_at')


# ── Superficie administrativa V2 (web retirada; admin = Django RBAC) ─────────
# Grupo 'Botánico' (migración 0014): solo-view sobre diagnósticos, telemetría
# IoT y logs RAG. SuperAdmin (is_superuser) conserva acceso total.


@admin.register(AIDiagnostic)
class AIDiagnosticAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'diagnosis_label', 'confidence_score', 'analyzed_at')
    list_filter = ('diagnosis_label', 'analyzed_at')
    search_fields = ('user__username', 'diagnosis_label')
    readonly_fields = ('analyzed_at',)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'is_active', 'auth_token_expires_at')
    list_filter = ('status', 'is_active')
    search_fields = ('name', 'owner__username')
    readonly_fields = ('auth_token', 'auth_token_expires_at')


@admin.register(AmbientReading)
class AmbientReadingAdmin(admin.ModelAdmin):
    list_display = ('device', 'recorded_at', 'air_temperature', 'air_humidity', 'uv_index')
    list_filter = ('recorded_at',)
    readonly_fields = ('device', 'recorded_at')

    def has_add_permission(self, request):
        return False


@admin.register(SoilReading)
class SoilReadingAdmin(admin.ModelAdmin):
    list_display = ('binding', 'recorded_at', 'soil_humidity', 'ph_level')
    list_filter = ('recorded_at',)
    readonly_fields = ('binding', 'recorded_at')

    def has_add_permission(self, request):
        return False


@admin.register(SensorLog)
class SensorLogAdmin(admin.ModelAdmin):
    list_display = ('plant_id', 'recorded_at', 'soil_humidity')
    list_filter = ('recorded_at',)
    readonly_fields = ('plant_id', 'recorded_at')

    def has_add_permission(self, request):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Append-only: nadie crea ni borra desde el admin (ni SuperAdmin)."""

    list_display = ('action', 'user_id', 'ip_address', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('action', 'details')
    readonly_fields = ('user_id', 'action', 'timestamp', 'ip_address', 'details')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
