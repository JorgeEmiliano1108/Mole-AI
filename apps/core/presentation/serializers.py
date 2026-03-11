from rest_framework import serializers
from django.utils import timezone


class SensorReadingSerializer(serializers.Serializer):
    """
    Validates a single Wide-Table reading from the ESP32 / Edge Node.
    Fields match sensor_logs columns exactly (no EAV).
    """
    plant_id = serializers.UUIDField()
    recorded_at = serializers.DateTimeField(required=False, default=timezone.now)
    soil_humidity = serializers.FloatField(required=False, allow_null=True, default=None)
    air_temperature = serializers.FloatField(required=False, allow_null=True, default=None)
    uv_index = serializers.FloatField(required=False, allow_null=True, default=None)
    light_level = serializers.FloatField(required=False, allow_null=True, default=None)
    ph_level = serializers.FloatField(
        required=False, allow_null=True, default=None,
        min_value=0.0, max_value=14.0,
        help_text="pH from TFLite CNN regression (HSV colorimetry).",
    )

    # At least one sensor column must be provided
    def validate(self, attrs):
        sensor_fields = [
            'soil_humidity', 'air_temperature', 'uv_index',
            'light_level', 'ph_level',
        ]
        if not any(attrs.get(f) is not None for f in sensor_fields):
            raise serializers.ValidationError(
                "Al menos un campo de sensor debe tener valor."
            )
        return attrs


class SensorBatchSerializer(serializers.Serializer):
    """
    Bulk sync payload from the Edge Node Store-and-Forward daemon.
    Max 500 readings per push to protect Supabase free tier.
    """
    batch = serializers.ListField(
        child=SensorReadingSerializer(),
        min_length=1,
        max_length=500,
    )


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


# Sensor columns available for query filtering
SENSOR_COLUMNS = [
    'soil_humidity', 'air_temperature', 'uv_index', 'light_level', 'ph_level',
]


class SensorDataQuerySerializer(serializers.Serializer):
    hours_ago = serializers.IntegerField(min_value=1, max_value=168, default=24)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=50)


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