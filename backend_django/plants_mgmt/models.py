from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .managers import (
    PlantManager, SensorDataManager, DiagnosisManager, 
    PlantImageManager, KnowledgeDocumentManager
)

class Plant(models.Model):
    """Modelo para representar una planta monitoreada"""
    
    PLANT_TYPE_CHOICES = [
        ('chile', 'Chile (Capsicum)'),
        ('maiz', 'Maíz (Zea mays)'),
        ('aguacate', 'Aguacate (Persea americana)'),
        ('tomate', 'Tomate (Solanum lycopersicum)'),
        ('endemica_mexicana', 'Planta endémica mexicana'),
        ('desconocida', 'Planta no identificada'),
    ]
    
    STATUS_CHOICES = [
        ('healthy', 'Sana'),
        ('stress_water', 'Estrés hídrico'),
        ('pest_detection', 'Plagas detectadas'),
        ('nutrient_deficiency', 'Deficiencia nutricional'),
        ('multiple_issues', 'Múltiples problemas'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nombre de la planta")
    plant_type = models.CharField(
        max_length=20, 
        choices=PLANT_TYPE_CHOICES, 
        default='desconocida',
        verbose_name="Tipo de planta"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='healthy',
        verbose_name="Estado de salud"
    )
    description = models.TextField(blank=True, verbose_name="Descripción")
    location = models.CharField(max_length=200, blank=True, verbose_name="Ubicación")
    planted_date = models.DateField(verbose_name="Fecha de siembra")
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Propietario"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use custom manager
    objects = PlantManager()
    
    class Meta:
        verbose_name = "Planta"
        verbose_name_plural = "Plantas"
        ordering = ['-created_at']
        indexes = [
            # Performance indexes for common query patterns
            models.Index(fields=['owner', 'created_at'], name='idx_plant_owner_created'),
            models.Index(fields=['plant_type', 'status', 'created_at'], name='idx_plant_type_status'),
            models.Index(fields=['status', 'created_at'], name='idx_plant_status_time'),
            # Partial index for active plants only
            models.Index(
                fields=['created_at'],
                name='idx_plant_active',
                condition=models.Q(status__in=['healthy', 'stress_water', 'pest_detection'])
            ),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_plant_type_display()})"
    
    def get_latest_diagnosis(self):
        """Obtiene el diagnóstico más reciente"""
        return self.diagnoses.order_by('-created_at').first()
    
    def get_days_since_planting(self):
        """Calcula días desde la siembra"""
        return (timezone.now().date() - self.planted_date).days

class SensorData(models.Model):
    """Modelo para almacenar datos de sensores del ESP32"""
    
    device_id = models.CharField(max_length=50, verbose_name="ID del dispositivo")
    plant = models.ForeignKey(
        Plant, 
        on_delete=models.CASCADE, 
        related_name='sensor_readings',
        verbose_name="Planta"
    )
    humidity = models.FloatField(verbose_name="Humedad ambiental (%)")
    temperature = models.FloatField(verbose_name="Temperatura (°C)")
    ph = models.FloatField(verbose_name="pH del suelo")
    uv_index = models.FloatField(verbose_name="Índice UV")
    soil_moisture = models.FloatField(verbose_name="Humedad del suelo (%)")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Dato de sensor"
        verbose_name_plural = "Datos de sensores"
        ordering = ['-timestamp']
        indexes = [
            # Time-series indexes for IoT workloads
            models.Index(fields=['device_id', 'timestamp'], name='idx_sensor_device_time'),
            models.Index(fields=['plant', 'timestamp'], name='idx_sensor_plant_time'),
            models.Index(fields=['timestamp', 'plant'], name='idx_sensor_time_plant'),
            # Additional performance indexes
            models.Index(fields=['timestamp', 'humidity', 'temperature'], name='idx_sensor_metrics'),
        ]
    
    def __str__(self):
        return f"Sensor {self.device_id} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class Diagnosis(models.Model):
    """Modelo para almacenar diagnósticos de IA"""
    
    URGENCY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]
    
    plant = models.ForeignKey(
        Plant, 
        on_delete=models.CASCADE, 
        related_name='diagnoses',
        verbose_name="Planta"
    )
    sensor_data = models.ForeignKey(
        SensorData, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Datos de sensores"
    )
    
    # Resultados de análisis
    vision_analysis = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name="Análisis de visión"
    )
    rag_context = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name="Contexto RAG"
    )
    diagnosis_text = models.TextField(verbose_name="Diagnóstico")
    treatment_plan = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name="Plan de tratamiento"
    )
    urgency_level = models.CharField(
        max_length=10, 
        choices=URGENCY_CHOICES, 
        default='low',
        verbose_name="Nivel de urgencia"
    )
    confidence = models.FloatField(
        default=0.0,
        verbose_name="Confianza del diagnóstico"
    )
    recommendations = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name="Recomendaciones"
    )
    
    # Metadatos
    processing_time = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name="Tiempo de procesamiento (seg)"
    )
    ai_model_version = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Versión del modelo de IA"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Diagnóstico"
        verbose_name_plural = "Diagnósticos"
        ordering = ['-created_at']
        indexes = [
            # Critical performance indexes for diagnosis queries
            models.Index(fields=['plant', 'created_at'], name='idx_diagnosis_plant_time'),
            models.Index(fields=['urgency_level', 'created_at'], name='idx_diagnosis_urgency_time'),
            models.Index(fields=['confidence', 'created_at'], name='idx_diagnosis_confidence'),
            # Additional performance indexes
            models.Index(fields=['urgency_level', 'created_at'], name='idx_diagnosis_urgency'),
            models.Index(fields=['confidence', 'created_at'], name='idx_diagnosis_confidence'),
            models.Index(fields=['ai_model_version', 'created_at'], name='idx_diagnosis_model'),
        ]
    
    def __str__(self):
        return f"Diagnóstico {self.id} - {self.plant.name} ({self.created_at.strftime('%Y-%m-%d')})"
    
    def get_urgency_display_color(self):
        """Devuelve color Bootstrap para el nivel de urgencia"""
        colors = {
            'low': 'success',
            'medium': 'warning', 
            'high': 'danger',
            'critical': 'dark'
        }
        return colors.get(self.urgency_level, 'secondary')

class PlantImage(models.Model):
    """Modelo para almacenar imágenes de las plantas"""
    
    IMAGE_TYPE_CHOICES = [
        ('rgb', 'RGB (Color)'),
        ('infrared', 'Infrarroja (NoIR)'),
    ]
    
    plant = models.ForeignKey(
        Plant, 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name="Planta"
    )
    image = models.ImageField(
        upload_to='plant_images/%Y/%m/', 
        verbose_name="Imagen"
    )
    image_type = models.CharField(
        max_length=10, 
        choices=IMAGE_TYPE_CHOICES, 
        default='rgb',
        verbose_name="Tipo de imagen"
    )
    analysis_result = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name="Resultado del análisis"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Imagen de planta"
        verbose_name_plural = "Imágenes de plantas"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Imagen de {self.plant.name} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_absolute_url(self):
        """URL absoluta de la imagen"""
        return self.image.url if self.image else ""

class KnowledgeDocument(models.Model):
    """Modelo para documentos de conocimiento RAG"""
    
    title = models.CharField(max_length=200, verbose_name="Título")
    content = models.TextField(verbose_name="Contenido")
    metadata = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name="Metadatos"
    )
    plant_types = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Tipos de planta separados por comas",
        verbose_name="Tipos de planta"
    )
    tags = models.CharField(
        max_length=300, 
        blank=True, 
        help_text="Etiquetas separadas por comas",
        verbose_name="Etiquetas"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Documento de conocimiento"
        verbose_name_plural = "Documentos de conocimiento"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_plant_types_list(self):
        """Devuelve lista de tipos de planta"""
        return [pt.strip() for pt in self.plant_types.split(',') if pt.strip()]
    
    def get_tags_list(self):
        """Devuelve lista de etiquetas"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]