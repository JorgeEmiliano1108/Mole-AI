from rest_framework import serializers
from .models import Plant, SensorData, Diagnosis, PlantImage, KnowledgeDocument

class PlantSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Plant"""
    
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    plant_type_display = serializers.CharField(source='get_plant_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_since_planting = serializers.SerializerMethodField()
    latest_diagnosis = serializers.SerializerMethodField()
    
    class Meta:
        model = Plant
        fields = [
            'id', 'name', 'plant_type', 'plant_type_display', 'status', 'status_display',
            'description', 'location', 'planted_date', 'owner', 'owner_name',
            'days_since_planting', 'latest_diagnosis', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_days_since_planting(self, obj):
        return obj.get_days_since_planting()
    
    def get_latest_diagnosis(self, obj):
        latest = obj.get_latest_diagnosis()
        if latest:
            return {
                'id': latest.id,
                'diagnosis_text': latest.diagnosis_text,
                'urgency_level': latest.urgency_level,
                'created_at': latest.created_at
            }
        return None

class SensorDataSerializer(serializers.ModelSerializer):
    """Serializer para el modelo SensorData"""
    
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    
    class Meta:
        model = SensorData
        fields = [
            'id', 'device_id', 'plant', 'plant_name', 'humidity', 'temperature',
            'ph', 'uv_index', 'soil_moisture', 'timestamp'
        ]
        read_only_fields = ['timestamp']

class DiagnosisSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Diagnosis"""
    
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_level_display', read_only=True)
    urgency_color = serializers.CharField(source='get_urgency_display_color', read_only=True)
    
    class Meta:
        model = Diagnosis
        fields = [
            'id', 'plant', 'plant_name', 'sensor_data', 'vision_analysis',
            'rag_context', 'diagnosis_text', 'treatment_plan', 'urgency_level',
            'urgency_display', 'urgency_color', 'confidence', 'recommendations',
            'processing_time', 'ai_model_version', 'created_at'
        ]
        read_only_fields = ['created_at']

class PlantImageSerializer(serializers.ModelSerializer):
    """Serializer para el modelo PlantImage"""
    
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    image_type_display = serializers.CharField(source='get_image_type_display', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PlantImage
        fields = [
            'id', 'plant', 'plant_name', 'image', 'image_url', 'image_type',
            'image_type_display', 'analysis_result', 'uploaded_at'
        ]
        read_only_fields = ['uploaded_at']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.get_absolute_url()

class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    """Serializer para el modelo KnowledgeDocument"""
    
    plant_types_list = serializers.SerializerMethodField()
    tags_list = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowledgeDocument
        fields = [
            'id', 'title', 'content', 'metadata', 'plant_types', 'plant_types_list',
            'tags', 'tags_list', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_plant_types_list(self, obj):
        return obj.get_plant_types_list()
    
    def get_tags_list(self, obj):
        return obj.get_tags_list()

# Serializers para operaciones de IA
class ImageAnalysisRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de análisis de imagen"""
    
    image = serializers.ImageField()
    analysis_type = serializers.ChoiceField(
        choices=['rgb', 'infrared'],
        default='rgb'
    )
    plant_context = serializers.CharField(required=False, allow_blank=True)

class SensorDataRequestSerializer(serializers.Serializer):
    """Serializer para datos de sensores del ESP32"""
    
    device_id = serializers.CharField(max_length=50)
    plant_id = serializers.IntegerField()
    humidity = serializers.FloatField(min_value=0, max_value=100)
    temperature = serializers.FloatField(min_value=-50, max_value=60)
    ph = serializers.FloatField(min_value=0, max_value=14)
    uv_index = serializers.FloatField(min_value=0)
    soil_moisture = serializers.FloatField(min_value=0, max_value=100)

class DiagnosisRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de diagnóstico completo"""
    
    plant_id = serializers.IntegerField()
    sensor_data = SensorDataRequestSerializer(required=False)
    image = serializers.ImageField(required=False)
    analysis_type = serializers.ChoiceField(
        choices=['rgb', 'infrared'],
        required=False
    )
    plant_context = serializers.CharField(required=False, allow_blank=True)

class EmergencyDiagnosisRequestSerializer(serializers.Serializer):
    """Serializer para diagnóstico de emergencia"""
    
    plant_id = serializers.IntegerField()
    sensor_data = SensorDataRequestSerializer()
    image = serializers.ImageField(required=False)
    analysis_type = serializers.ChoiceField(
        choices=['rgb', 'infrared'],
        required=False
    )

# Serializers para respuestas de IA
class AIAnalysisResponseSerializer(serializers.Serializer):
    """Serializer para respuestas de servicios de IA"""
    
    success = serializers.BooleanField()
    data = serializers.JSONField()
    error_message = serializers.CharField(required=False, allow_blank=True)
    processing_time = serializers.FloatField(required=False)

class VisionAnalysisResultSerializer(serializers.Serializer):
    """Serializer para resultados de análisis de visión"""
    
    image_id = serializers.CharField()
    analysis_type = serializers.CharField()
    plant_type = serializers.CharField()
    health_status = serializers.CharField()
    confidence = serializers.FloatField()
    detections = serializers.ListField()
    recommendations = serializers.ListField()

class RAGDiagnosisResultSerializer(serializers.Serializer):
    """Serializer para resultados de diagnóstico RAG"""
    
    diagnosis_id = serializers.CharField()
    plant_id = serializers.CharField()
    diagnosis = serializers.CharField()
    urgency_level = serializers.CharField()
    confidence = serializers.FloatField()
    treatment_plan = serializers.ListField()
    recommendations = serializers.ListField()
    context_used = serializers.ListField()