from django.db import models
from django.contrib.auth import get_user_model
from pgvector.django import VectorField

User = get_user_model()


class LLMRequest(models.Model):
    """
    Model for tracking Large Language Model requests and responses.
    """
    
    REQUEST_TYPES = [
        ('plant_care_advice', 'Plant Care Advice'),
        ('diagnostic_explanation', 'Diagnostic Explanation'),
        ('treatment_recommendation', 'Treatment Recommendation'),
        ('knowledge_query', 'Knowledge Query'),
        ('chat_conversation', 'Chat Conversation'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]
    
    # Primary key and relationships
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, db_index=True)
    
    # Request information
    request_type = models.CharField(max_length=30, choices=REQUEST_TYPES)
    prompt = models.TextField()
    context = models.JSONField(default=dict, blank=True)  # Additional context for the LLM
    
    # Model configuration
    model_name = models.CharField(max_length=50)  # e.g., 'gpt-4', 'claude-3'
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=1000)
    
    # Response information
    response = models.TextField(blank=True)
    response_metadata = models.JSONField(default=dict, blank=True)
    token_usage = models.JSONField(default=dict, blank=True)
    
    # Performance metrics
    processing_time_ms = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Quality metrics
    user_rating = models.IntegerField(null=True, blank=True)  # 1-5 stars
    feedback = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        """Override save para evitar crash por processing_time_ms nulo"""
        if self.processing_time_ms is None:
            self.processing_time_ms = 0
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'llm_requests'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session_id', 'created_at']),
            models.Index(fields=['request_type', 'status']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"LLM Request {self.id} - {self.request_type} ({self.status})"


class CNNInference(models.Model):
    """
    Model for tracking Convolutional Neural Network image inferences.
    """
    
    MODEL_TYPES = [
        ('disease_detection', 'Disease Detection'),
        ('plant_identification', 'Plant Identification'),
        ('pest_detection', 'Pest Detection'),
        ('nutrient_deficiency', 'Nutrient Deficiency'),
        ('growth_stage', 'Growth Stage Analysis'),
    ]
    
    INFERENCE_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Primary key and relationships
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    request_id = models.CharField(max_length=100, db_index=True)
    
    # Input information
    image_url = models.URLField()
    image_metadata = models.JSONField(default=dict, blank=True)
    model_type = models.CharField(max_length=30, choices=MODEL_TYPES)
    model_name = models.CharField(max_length=50)
    model_version = models.CharField(max_length=20)
    
    # Preprocessing information
    image_size = models.JSONField(default=dict)  # {'width': 224, 'height': 224}
    preprocessing_steps = models.JSONField(default=list, blank=True)
    
    # Inference results
    predictions = models.JSONField(default=list)  # List of prediction objects
    confidence_scores = models.JSONField(default=list)  # List of confidence scores
    top_prediction = models.JSONField(default=dict)  # Highest confidence prediction
    
    # Feature extraction
    features_vector = VectorField(dimensions=512, null=True, blank=True)  # CNN features
    embedding_vector = VectorField(dimensions=1536, null=True, blank=True)  # CLIP embedding
    # features_vector = models.TextField(null=True, blank=True)  # Temporary field type
    # embedding_vector = models.TextField(null=True, blank=True)  # Temporary field type
    
    # Performance metrics
    inference_time_ms = models.IntegerField()
    memory_usage_mb = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=INFERENCE_STATUS, default='pending')
    error_message = models.TextField(blank=True)
    
    # Quality validation
    human_verified = models.BooleanField(default=False)
    human_prediction = models.JSONField(default=dict, blank=True)
    verification_accuracy = models.FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'cnn_inferences'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['model_type', 'status']),
            models.Index(fields=['request_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"CNN Inference {self.id} - {self.model_type} ({self.status})"


class ModelPerformance(models.Model):
    """
    Model for tracking AI model performance metrics over time.
    """
    
    MODEL_CATEGORIES = [
        ('llm', 'Large Language Model'),
        ('cnn', 'Convolutional Neural Network'),
        ('transformer', 'Transformer Model'),
        ('ensemble', 'Ensemble Model'),
    ]
    
    # Primary key
    id = models.BigAutoField(primary_key=True)
    
    # Model identification
    model_name = models.CharField(max_length=50)
    model_category = models.CharField(max_length=20, choices=MODEL_CATEGORIES)
    model_version = models.CharField(max_length=20)
    
    # Performance metrics
    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    auc_score = models.FloatField(null=True, blank=True)
    
    # Latency metrics
    avg_response_time_ms = models.FloatField()
    p95_response_time_ms = models.FloatField()
    p99_response_time_ms = models.FloatField()
    
    # Resource usage
    avg_memory_usage_mb = models.FloatField()
    peak_memory_usage_mb = models.FloatField()
    cpu_usage_percent = models.FloatField()
    
    # Usage statistics
    total_requests = models.IntegerField(default=0)
    successful_requests = models.IntegerField(default=0)
    failed_requests = models.IntegerField(default=0)
    
    # Time period
    metrics_date = models.DateField()
    metrics_hour = models.IntegerField(null=True, blank=True)  # For hourly metrics
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'model_performance'
        unique_together = ['model_name', 'model_version', 'metrics_date', 'metrics_hour']
        indexes = [
            models.Index(fields=['model_category', 'metrics_date']),
            models.Index(fields=['model_name', 'metrics_date']),
        ]
        ordering = ['-metrics_date', '-metrics_hour']
    
    def __str__(self):
        return f"{self.model_name} v{self.model_version} - {self.metrics_date}"


class AIModelConfiguration(models.Model):
    """
    Model for storing AI model configurations and parameters.
    """
    
    MODEL_TYPES = [
        ('llm', 'Large Language Model'),
        ('cnn', 'Convolutional Neural Network'),
        ('transformer', 'Transformer Model'),
        ('custom', 'Custom Model'),
    ]
    
    # Primary key
    id = models.BigAutoField(primary_key=True)
    
    # Model identification
    model_name = models.CharField(max_length=50, unique=True)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    model_version = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    
    # Configuration parameters
    parameters = models.JSONField(default=dict)
    default_settings = models.JSONField(default=dict)
    
    # Resource requirements
    min_memory_mb = models.IntegerField()
    recommended_memory_mb = models.IntegerField()
    gpu_required = models.BooleanField(default=False)
    gpu_memory_mb = models.IntegerField(null=True, blank=True)
    
    # Deployment settings
    endpoint_url = models.URLField(blank=True)
    api_key_required = models.BooleanField(default=False)
    rate_limit_per_minute = models.IntegerField(default=60)
    
    # Status and availability
    is_active = models.BooleanField(default=True)
    is_production_ready = models.BooleanField(default=False)
    health_check_url = models.URLField(blank=True)
    last_health_check = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_model_configurations'
        indexes = [
            models.Index(fields=['model_type', 'is_active']),
            models.Index(fields=['is_production_ready']),
        ]
        ordering = ['model_name']
    
    def __str__(self):
        return f"{self.model_name} ({self.model_type})"
