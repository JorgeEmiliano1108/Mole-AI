from rest_framework import serializers
from django.core.exceptions import ValidationError
from ..infrastructure.repositories.models import SensorLog, PlantKnowledge, AIDiagnostic


class SensorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorLog
        fields = [
            'device_id', 'sensor_type', 'value', 'unit', 
            'plant_id', 'location_x', 'location_y', 'location_z'
        ]
    
    def validate_sensor_type(self, value):
        valid_types = [choice[0] for choice in SensorLog.SENSOR_TYPES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid sensor type. Must be one of: {valid_types}"
            )
        return value
    
    def validate_value(self, value):
        if not isinstance(value, (int, float)):
            raise serializers.ValidationError("Value must be a number")
        if value < -1000 or value > 1000:
            raise serializers.ValidationError("Value out of reasonable range")
        return value
    
    def validate_device_id(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Device ID cannot be empty")
        if len(value) > 100:
            raise serializers.ValidationError("Device ID too long")
        return value.strip()


class DiagnosticRequestSerializer(serializers.Serializer):
    plant_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    model_type = serializers.ChoiceField(
        choices=[
            ('disease_detection', 'Disease Detection'),
            ('plant_identification', 'Plant Identification'),
            ('pest_detection', 'Pest Detection'),
            ('nutrient_deficiency', 'Nutrient Deficiency'),
            ('growth_stage', 'Growth Stage Analysis'),
        ],
        default='disease_detection'
    )
    image = serializers.ImageField(required=True)
    
    def validate_image(self, value):
        # Validar tamaño de archivo (max 10MB)
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Image too large. Max size is 10MB")
        
        # Validar tipo de archivo
        valid_types = ['image/jpeg', 'image/png', 'image/webp']
        if value.content_type not in valid_types:
            raise serializers.ValidationError(
                f"Invalid image type. Must be one of: {valid_types}"
            )
        
        return value


class LLMChatRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=2000, required=True)
    request_type = serializers.ChoiceField(
        choices=[
            ('plant_care_advice', 'Plant Care Advice'),
            ('diagnostic_explanation', 'Diagnostic Explanation'),
            ('treatment_recommendation', 'Treatment Recommendation'),
            ('knowledge_query', 'Knowledge Query'),
            ('chat_conversation', 'Chat Conversation'),
        ],
        default='chat_conversation'
    )
    plant_species = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_prompt(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Prompt cannot be empty")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Prompt too short")
        return value.strip()


class SensorDataQuerySerializer(serializers.Serializer):
    hours_ago = serializers.IntegerField(min_value=1, max_value=168, default=24)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=50)
    sensor_types = serializers.ListField(
        child=serializers.ChoiceField(choices=[choice[0] for choice in SensorLog.SENSOR_TYPES]),
        required=False,
        allow_empty=True
    )
    
    def validate_sensor_types(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("Too many sensor types specified")
        return value


class PlantKnowledgeQuerySerializer(serializers.Serializer):
    plant_species = serializers.CharField(max_length=100, required=False, allow_blank=True)
    knowledge_type = serializers.ChoiceField(
        choices=[
            ('care_guide', 'Care Guide'),
            ('disease_info', 'Disease Information'),
            ('treatment', 'Treatment Protocol'),
            ('growth_stage', 'Growth Stage Info'),
            ('environmental', 'Environmental Requirements'),
        ],
        required=False,
        allow_blank=True
    )