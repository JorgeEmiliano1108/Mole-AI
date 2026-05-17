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
    soil_humidity = models.FloatField(null=True, blank=True, db_index=True)
    air_humidity = models.FloatField(null=True, blank=True)
    air_temperature = models.FloatField(null=True, blank=True, db_index=True)
    uv_index = models.FloatField(null=True, blank=True, db_index=True)
    light_level = models.FloatField(null=True, blank=True)
    # ── CNN-inferred (populated async by AI micro-service PATCH)
    ph_level = models.FloatField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'sensor_logs'
        managed = True
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['plant_id', 'recorded_at']),
        ]

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
    # Referencia al usuario que solicitó el diagnóstico (nullable para integraciones M2M)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_diagnostics')
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
    
    # Compatibility properties for older code expecting these attributes
    @property
    def severity(self):
        if self.metadata and isinstance(self.metadata, dict):
            return self.metadata.get('severity')
        return None

    @property
    def condition_name(self):
        return self.diagnosis_label or (self.metadata.get('condition_name') if self.metadata and isinstance(self.metadata, dict) else None)

    @property
    def condition_description(self):
        return (self.metadata.get('raw_output') if self.metadata and isinstance(self.metadata, dict) else None)

    # Alias for created_at used by some views
    @property
    def created_at(self):
        return self.analyzed_at


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

# ---------------------------------------------------------------------------
# IoT NODE – conexión de dispositivos ESP32
# ---------------------------------------------------------------------------
class IoTNode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='iot_nodes')
    name = models.CharField(max_length=128)
    method = models.CharField(max_length=12, choices=[('wifi','Wi‑Fi'),('bluetooth','Bluetooth')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'iot_nodes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.method})"


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

class AuditLog(models.Model):
    """
    Tabla Inmutable de Auditoría para trazabilidad de acciones críticas 
    alineada a la normativa MoProSoft y lineamientos DevSecOps.
    """
    id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField(null=True, blank=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True)

    class Meta:
        db_table = 'audit_logs'
        managed = True
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.action} by User {self.user_id}"

    def delete(self, *args, **kwargs):
        raise PermissionError("MoProSoft Compliance: Audit logs are immutable and cannot be deleted.")

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("MoProSoft Compliance: Audit logs are append-only and cannot be modified.")
        super().save(*args, **kwargs)

# ---------------------------------------------------------------------------
# IOT DEEP MODELS (REFACTORING 1:N)
# ---------------------------------------------------------------------------
import uuid

class Device(models.Model):
    """El Microcontrolador físico (Gateway ESP32)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    auth_token = models.CharField(max_length=128, unique=True, help_text="Bearer token")
    status = models.CharField(max_length=20, default='offline')
    created_at = models.DateTimeField(auto_now_add=True)

class Plant(models.Model):
    """Zona de suelo cultivado monitoreada por un pin de un Device"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='plants')
    hardware_pin = models.CharField(max_length=10, help_text="Ej: '32', 'A0'")
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('device', 'hardware_pin')

class AmbientReading(models.Model):
    """Telemetría del entorno físico (DHT22 / LTR390)"""
    id = models.BigAutoField(primary_key=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='ambient_readings')
    recorded_at = models.DateTimeField(default=timezone.now)
    air_temperature = models.FloatField(null=True, blank=True)
    air_humidity = models.FloatField(null=True, blank=True)
    light_level = models.FloatField(null=True, blank=True)
    uv_index = models.FloatField(null=True, blank=True)

class SoilReading(models.Model):
    """Telemetría específica de una Planta (Suelo)"""
    id = models.BigAutoField(primary_key=True)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='soil_readings')
    recorded_at = models.DateTimeField(default=timezone.now)
    soil_humidity = models.FloatField()
    ph_level = models.FloatField(null=True, blank=True)
