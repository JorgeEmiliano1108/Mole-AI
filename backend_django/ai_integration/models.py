"""
Modelos Django para integración con servicio IA (Phi-3.5)
"""
import json
from datetime import datetime
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class PlantImage(models.Model):
    """Modelo para almacenar imágenes de plantas"""
    image_file = models.ImageField(upload_to='plant_images/')
    filename = models.CharField(max_length=255)
    format = models.CharField(max_length=10, default='jpeg')
    size_bytes = models.PositiveIntegerField(null=True, blank=True)
    image_base64 = models.TextField(blank=True, null=True)  # Para imágenes pequeñas
    storage_path = models.CharField(max_length=500, blank=True)  # Para imágenes grandes
    
    # Metadatos
    captured_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"Image_{self.id}_{self.filename}"


class SensorData(models.Model):
    """Modelo para datos de sensores"""
    plant = models.ForeignKey('Plant', on_delete=models.CASCADE, related_name='sensor_readings')
    
    # Datos del sensor
    ph = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(14.0)],
        help_text="pH del suelo (0-14)"
    )
    humedad = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Humedad relativa (%) (0-100)"
    )
    temperatura = models.FloatField(
        validators=[MinValueValidator(-50.0), MaxValueValidator(60.0)],
        help_text="Temperatura ambiente (°C) (-50 a 60)"
    )
    uv = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(15.0)],
        help_text="Índice UV (0-15)"
    )
    
    # Datos adicionales para futuras expansiones
    conductividad_electrica = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0)],
        help_text="Conductividad eléctrica del suelo"
    )
    humedad_suelo = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Humedad del suelo (%) (0-100)"
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['plant', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"SensorData_{self.plant.id}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}"


class AIRequest(models.Model):
    """Modelo para registrar solicitudes al servicio IA"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallo'),
    ]
    
    # Datos de la solicitud
    plant = models.ForeignKey('Plant', on_delete=models.CASCADE)
    image = models.ForeignKey(PlantImage, on_delete=models.CASCADE)
    sensor_data = models.ForeignKey(SensorData, on_delete=models.CASCADE)
    
    # Control de proceso
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_data = models.JSONField(default=dict)
    
    # Respuesta del servicio IA
    response_data = models.JSONField(default=dict, null=True, blank=True)
    processing_time = models.FloatField(help_text="Tiempo de procesamiento en segundos", null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Metadatos
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['plant', '-created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"AIRequest_{self.id}_{self.plant.nombre}"


class DiagnosisResult(models.Model):
    """Modelo para almacenar resultados de diagnósticos"""
    ESTADO_CHOICES = [
        ('Sana', 'Sana'),
        ('Atención', 'Atención'),
        ('Peligro', 'Peligro'),
    ]
    
    # Relaciones
    plant = models.ForeignKey('Plant', on_delete=models.CASCADE, related_name='diagnoses')
    ai_request = models.OneToOneField(AIRequest, on_delete=models.CASCADE)
    
    # Resultados del diagnóstico
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    confianza = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Nivel de confianza (0.0-1.0)"
    )
    especie = models.CharField(max_length=100, blank=True)
    sintomas = models.TextField(help_text="Síntomas observados")
    diagnostico = models.TextField(help_text="Diagnóstico técnico")
    recomendaciones = models.TextField(help_text="Recomendaciones")
    fuentes = models.TextField(blank=True, help_text="Fuentes consultadas")
    
    # Metadatos técnicos
    modelo_utilizado = models.CharField(max_length=100, default="Phi-3.5 Vision-Instruct Q4")
    tiempo_inferencia = models.FloatField(null=True, blank=True)
    requiere_accion_humana = models.BooleanField(default=False)
    
    # Datos estructurados
    datos_sensores = models.JSONField(default=dict)
    contexto_conocimiento = models.JSONField(default=dict)
    resultado_vision = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['estado', '-created_at']),
            models.Index(fields=['confianza']),
            models.Index(fields=['plant', '-created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Diagnosis_{self.id}_{self.plant.nombre}_{self.estado}"
    
    @property
    def es_confiable(self) -> bool:
        """Determina si el diagnóstico es confiable"""
        return self.confianza >= 0.85
    
    @property
    def nivel_riesgo(self) -> str:
        """Retorna nivel de riesgo basado en estado y confianza"""
        if self.estado == 'Peligro' and self.es_confiable:
            return "ALTO"
        elif self.estado == 'Atención' or not self.es_confiable:
            return "MEDIO"
        else:
            return "BAJO"


class AIServiceConfig(models.Model):
    """Configuración del servicio IA externo"""
    service_name = models.CharField(max_length=100, default="Mole AI Service")
    base_url = models.URLField(help_text="URL base del servicio IA")
    api_key = models.CharField(max_length=500, blank=True, help_text="API Key para autenticación")
    
    # Configuración del modelo
    model_name = models.CharField(max_length=100, default="microsoft/Phi-3.5-vision-instruct")
    max_retries = models.IntegerField(default=3)
    timeout_seconds = models.IntegerField(default=300)
    
    # Estado del servicio
    is_active = models.BooleanField(default=True)
    last_health_check = models.DateTimeField(null=True, blank=True)
    health_status = models.CharField(max_length=20, default='unknown')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.service_name} ({'Active' if self.is_active else 'Inactive'})"


class AIRequestLog(models.Model):
    """Log detallado de solicitudes al servicio IA"""
    ai_request = models.ForeignKey(AIRequest, on_delete=models.CASCADE, related_name='logs')
    
    # Timestamp y duración
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_ms = models.FloatField(help_text="Duración en milisegundos")
    
    # Detalles de la solicitud
    endpoint = models.CharField(max_length=200)
    request_payload = models.JSONField(default=dict)
    response_status_code = models.IntegerField()
    response_payload = models.JSONField(default=dict, null=True, blank=True)
    
    # Errores
    error_type = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ai_request', '-timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['response_status_code']),
        ]