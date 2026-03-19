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
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from pgvector.django import VectorField

User = get_user_model()


class SensorLog(models.Model):
    """
    Wide-table model for sensor readings.
    """

    id = models.BigAutoField(primary_key=True)
    plant_id = models.UUIDField(db_index=True)
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)

    # Wide-table sensor columns  ── ESP32 physical sensors
    soil_humidity = models.FloatField(null=True, blank=True)
    air_humidity = models.FloatField(null=True, blank=True)
    air_temperature = models.FloatField(null=True, blank=True)
    uv_index = models.FloatField(null=True, blank=True)
    light_level = models.FloatField(null=True, blank=True)
    # ── CNN-inferred (populated async by AI micro-service PATCH)
    ph_level = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'sensor_logs'
        managed = True
        ordering = ['-recorded_at']

    def __str__(self):
        return f"plant={self.plant_id} at {self.recorded_at}"


class BotanicalKnowledge(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    content = models.TextField(null=True, blank=True)
    source_url = models.TextField(null=True, blank=True)
    chunk_metadata = models.JSONField(null=True, blank=True)
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    
    class Meta:
        db_table = 'botanical_knowledge'
        managed = True
    
    def __str__(self):
        return f"Knowledge {self.id}"


class AIDiagnostic(models.Model):
    import uuid
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plant_id = models.UUIDField(db_index=True)
    analyzed_at = models.DateTimeField(default=timezone.now, db_index=True)
    image_path = models.TextField(null=True, blank=True)
    diagnosis_label = models.TextField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'ai_diagnostics'
        managed = True
        ordering = ['-analyzed_at']
    
    def __str__(self):
        return f"{self.plant_id} - {self.diagnosis_label}"


class DiagnosticoGeolocalizado(models.Model):
    """
    Tabla para almacenar diagnósticos con coordenadas geográficas.
    Managed=True para que Django cree y migre esta tabla localmente (SQLite).
    """

    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    id = models.BigAutoField(primary_key=True)
    diagnostic = models.ForeignKey(AIDiagnostic, null=True, blank=True, on_delete=models.SET_NULL, related_name='geolocations')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    condition_name = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True, db_index=True)
    longitude = models.FloatField(null=True, blank=True, db_index=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diagnosticos_geolocalizados'
        managed = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.condition_name} @({self.latitude},{self.longitude})"


class FeedbackTicket(models.Model):
    """
    Tickets de feedback enviados por agricultores:
    reportes de errores de IA, sugerencias, bugs, etc.
    """

    TOPIC_CHOICES = [
        ('bug', 'Bug'),
        ('suggestion', 'Suggestion'),
        ('ai_error', 'AI Error'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback_tickets',
    )
    topic = models.CharField(max_length=20, choices=TOPIC_CHOICES)
    message = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='open',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feedback_tickets'
        managed = True
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.topic}] {self.user} — {self.status}"
