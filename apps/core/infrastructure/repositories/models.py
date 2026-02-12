from django.db import models
from django.contrib.auth import get_user_model
# from pgvector import VectorField  # Temporarily commented for setup

User = get_user_model()


class SensorLog(models.Model):
    """
    Model for sensor logs from plant monitoring devices.
    Maps to existing sensor_logs table in Supabase.
    """
    
    SENSOR_TYPES = [
        ('temperature', 'Temperature'),
        ('humidity', 'Humidity'),
        ('light', 'Light Intensity'),
        ('soil_moisture', 'Soil Moisture'),
        ('ph', 'pH Level'),
        ('nutrients', 'Nutrient Levels'),
    ]
    
    # Primary key and relationships
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    device_id = models.CharField(max_length=100, db_index=True)
    
    # Sensor data
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPES, db_index=True)
    value = models.FloatField()
    unit = models.CharField(max_length=10)  # e.g., '°C', '%', 'lux'
    
    # Location and metadata
    plant_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    location_x = models.FloatField(null=True, blank=True)  # GPS X coordinate
    location_y = models.FloatField(null=True, blank=True)  # GPS Y coordinate
    location_z = models.FloatField(null=True, blank=True)  # Height/depth
    
    # Timestamps
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sensor_logs'
        managed = False  # Don't let Django create/modify this table
        indexes = [
            models.Index(fields=['device_id', 'timestamp']),
            models.Index(fields=['plant_id', 'sensor_type', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.device_id} - {self.sensor_type}: {self.value}{self.unit} at {self.timestamp}"


class PlantKnowledge(models.Model):
    """
    Model for plant knowledge base with vector embeddings.
    Maps to existing plant_knowledge table with pgvector support.
    """
    
    KNOWLEDGE_TYPES = [
        ('care_guide', 'Care Guide'),
        ('disease_info', 'Disease Information'),
        ('treatment', 'Treatment Protocol'),
        ('growth_stage', 'Growth Stage Info'),
        ('environmental', 'Environmental Requirements'),
    ]
    
    # Primary key and content
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    knowledge_type = models.CharField(max_length=20, choices=KNOWLEDGE_TYPES, db_index=True)
    
    # Plant classification
    plant_species = models.CharField(max_length=100, db_index=True)
    plant_genus = models.CharField(max_length=50, db_index=True)
    plant_family = models.CharField(max_length=50, db_index=True)
    common_names = models.JSONField(default=list, blank=True)
    
    # Vector embedding for semantic search
    # embedding = VectorField(dimensions=1536)  # OpenAI embedding dimension - Temporarily commented
    embedding = models.TextField(null=True, blank=True)  # Temporary field type
    
    # Metadata
    source = models.CharField(max_length=100, blank=True)
    confidence_score = models.FloatField(default=0.0)
    language = models.CharField(max_length=10, default='en')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plant_knowledge'
        managed = False  # Don't let Django create/modify this table
        indexes = [
            models.Index(fields=['plant_species', 'knowledge_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.plant_species}"


class AIDiagnostic(models.Model):
    """
    Model for AI diagnostic results and recommendations.
    Maps to existing ai_diagnostics table.
    """
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    DIAGNOSTIC_TYPES = [
        ('disease', 'Disease Detection'),
        ('nutrient_deficiency', 'Nutrient Deficiency'),
        ('pest_infestation', 'Pest Infestation'),
        ('environmental_stress', 'Environmental Stress'),
        ('growth_analysis', 'Growth Analysis'),
    ]
    
    # Primary key and relationships
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    plant_id = models.CharField(max_length=100, db_index=True)
    
    # Diagnostic information
    diagnostic_type = models.CharField(max_length=30, choices=DIAGNOSTIC_TYPES)
    condition_name = models.CharField(max_length=200)
    condition_description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    
    # AI model information
    ai_model_used = models.CharField(max_length=50)
    confidence_score = models.FloatField()
    processing_time_ms = models.IntegerField()
    
    # Input data reference
    image_url = models.URLField(null=True, blank=True)
    sensor_data_reference = models.JSONField(default=dict, blank=True)
    
    # Recommendations
    recommendations = models.JSONField(default=list, blank=True)
    treatment_protocol = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_days = models.IntegerField(null=True, blank=True)
    
    # Status and resolution
    status = models.CharField(max_length=20, default='pending')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_diagnostics'
        managed = False  # Don't let Django create/modify this table
        indexes = [
            models.Index(fields=['plant_id', 'created_at']),
            models.Index(fields=['diagnostic_type', 'severity']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.plant_id} - {self.condition_name} ({self.severity})"
