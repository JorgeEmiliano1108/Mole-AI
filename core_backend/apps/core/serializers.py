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
from datetime import timedelta
from .models import IoTNode

from rest_framework import serializers
from django.utils import timezone

# ETSI EN 303 645 — Ventana anti-replay para ingesta directa de ESP32.
# Las lecturas deben tener un timestamp dentro de ±REPLAY_WINDOW del reloj UTC del servidor.
# Se añaden CLOCK_SKEW_TOLERANCE segundos de tolerancia por posible desincronización NTP.
REPLAY_WINDOW_SECONDS = 60
CLOCK_SKEW_TOLERANCE_SECONDS = 5


class SensorReadingSerializer(serializers.Serializer):
    """
    Validates a single Wide-Table reading from the ESP32 / Edge Node.
    Fields match sensor_logs columns exactly (no EAV).
    """
    plant_id = serializers.UUIDField()
    recorded_at = serializers.DateTimeField(required=False, default=timezone.now)
    soil_humidity = serializers.FloatField(required=False, allow_null=True, default=None)
    air_humidity = serializers.FloatField(required=False, allow_null=True, default=None)
    air_temperature = serializers.FloatField(required=False, allow_null=True, default=None)
    uv_index = serializers.FloatField(required=False, allow_null=True, default=None)
    light_level = serializers.FloatField(required=False, allow_null=True, default=None)
    ph_level = serializers.FloatField(
        required=False, allow_null=True, default=None,
        min_value=0.0, max_value=14.0,
        help_text="pH from TFLite CNN regression (HSV colorimetry).",
    )

    def validate_recorded_at(self, value):
        """
        ETSI EN 303 645 — Anti-replay validation.
        Rechaza lecturas cuyo timestamp difiera más de 60s (+5s tolerancia)
        del reloj UTC del servidor.  Mitiga ataques de replay donde un
        atacante reenvía payloads capturados anteriormente.

        NOTA: Esta validación aplica SOLO al endpoint single
        (POST /api/v1/sensor-data/).  El endpoint batch está exento
        porque el daemon Store-and-Forward acumula lecturas offline.
        """
        now = timezone.now()
        max_age = timedelta(seconds=REPLAY_WINDOW_SECONDS + CLOCK_SKEW_TOLERANCE_SECONDS)
        future_tolerance = timedelta(seconds=CLOCK_SKEW_TOLERANCE_SECONDS)

        if value < now - max_age:
            raise serializers.ValidationError(
                f"Timestamp rechazado: la lectura tiene más de "
                f"{REPLAY_WINDOW_SECONDS}s de antigüedad (anti-replay ETSI EN 303 645). "
                f"Sincronice el reloj NTP del dispositivo."
            )
        if value > now + future_tolerance:
            raise serializers.ValidationError(
                "Timestamp rechazado: la lectura tiene fecha futura. "
                "Sincronice el reloj NTP del dispositivo."
            )
        return value

    # At least one sensor column must be provided
    def validate(self, attrs):
        sensor_fields = [
            'soil_humidity', 'air_humidity', 'air_temperature',
            'uv_index', 'light_level', 'ph_level',
        ]
        if not any(attrs.get(f) is not None for f in sensor_fields):
            raise serializers.ValidationError(
                "Al menos un campo de sensor debe tener valor."
            )
        return attrs


class SensorBatchReadingSerializer(serializers.Serializer):
    """
    Individual reading inside a batch — WITHOUT anti-replay validation.
    The Store-and-Forward daemon sends readings accumulated offline;
    strict timestamp windows would reject legitimate offline data.
    """
    plant_id = serializers.UUIDField()
    recorded_at = serializers.DateTimeField(required=False, default=timezone.now)
    soil_humidity = serializers.FloatField(required=False, allow_null=True, default=None)
    air_humidity = serializers.FloatField(required=False, allow_null=True, default=None)
    air_temperature = serializers.FloatField(required=False, allow_null=True, default=None)
    uv_index = serializers.FloatField(required=False, allow_null=True, default=None)
    light_level = serializers.FloatField(required=False, allow_null=True, default=None)
    ph_level = serializers.FloatField(
        required=False, allow_null=True, default=None,
        min_value=0.0, max_value=14.0,
    )

    def validate(self, attrs):
        sensor_fields = [
            'soil_humidity', 'air_humidity', 'air_temperature',
            'uv_index', 'light_level', 'ph_level',
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
    Uses SensorBatchReadingSerializer (no anti-replay) for offline tolerance.
    """
    batch = serializers.ListField(
        child=SensorBatchReadingSerializer(),
        min_length=1,
        max_length=500,
    )


# ── Edge Node Compact Contract (1:N Refactoring) ────────────────────────────

class EdgeSoilItemSerializer(serializers.Serializer):
    """Single soil reading: {p: "32", v: 2847}"""
    p = serializers.CharField(max_length=10, help_text="Hardware pin identifier")
    v = serializers.FloatField(min_value=0, max_value=4095, help_text="Raw ADC value or calibrated %")


class EdgeFrameSerializer(serializers.Serializer):
    """
    Validates the compact JSON contract from ESP32 firmware (~180 bytes).
    Contract: {ts: epoch, ri: minutes, a: {t,h,l,u}, s: [{p,v}]}
    """
    ts = serializers.FloatField(help_text="Unix epoch timestamp")
    ri = serializers.IntegerField(
        min_value=1, max_value=120, required=False, default=5,
        help_text="Report interval in minutes",
    )
    a = serializers.DictField(required=False, allow_null=True, help_text="Ambient readings")
    s = EdgeSoilItemSerializer(many=True, required=False, default=list, help_text="Soil readings array")

    def validate_ts(self, value):
        """A4: Only reject timestamps from the FUTURE (> now + 5min). Past timestamps are 100% valid."""
        from django.utils import timezone as tz
        from datetime import datetime, timedelta
        naive_dt = datetime.fromtimestamp(value)
        aware_dt = tz.make_aware(naive_dt)
        if aware_dt > tz.now() + timedelta(minutes=5):
            raise serializers.ValidationError(
                "Timestamp rejected: future timestamp exceeds clock drift tolerance (>5min)."
            )
        return value

    def validate_a(self, value):
        """Expand compact ambient keys and validate ranges."""
        if value is None:
            return None
        KEY_MAP = {'t': 'air_temperature', 'h': 'air_humidity', 'l': 'light_level', 'u': 'uv_index'}
        RANGES = {
            'air_temperature': (-40.0, 80.0),
            'air_humidity': (0.0, 100.0),
            'light_level': (0.0, 65535.0),
            'uv_index': (0.0, 15.0),
        }
        expanded = {}
        for short_key, val in value.items():
            full_key = KEY_MAP.get(short_key)
            if full_key and val is not None:
                lo, hi = RANGES.get(full_key, (None, None))
                if lo is not None and not (lo <= float(val) <= hi):
                    raise serializers.ValidationError(
                        f"{full_key} ({val}) out of range [{lo}, {hi}]"
                    )
                expanded[full_key] = float(val)
        return expanded


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
            
        # Validación OWASP estricta (Magic Bytes) previniendo ejecutables camuflados
        header = value.read(2048)
        value.seek(0)
        
        is_jpeg = header.startswith(b'\xff\xd8\xff')
        is_png = header.startswith(b'\x89PNG\r\n\x1a\n')
        is_webp = header.startswith(b'RIFF') and header[8:12] == b'WEBP'
        
        if not (is_jpeg or is_png or is_webp):
            raise serializers.ValidationError("Firma de archivo inválida. Posible binario camuflado.")
            
        # Medida draconiana contra inyecciones directas de cabeceras
        if b'MZ' in header[:2] or b'\x7fELF' in header[:4]:
            raise serializers.ValidationError("Ejecutable malicioso detectado.")
            
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
from apps.core.models import SensorLog, AIDiagnostic

class HistorySerializer(serializers.Serializer):
    id = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=50) # 'sensor' or 'diagnostic'
    timestamp = serializers.DateTimeField()
    plant_id = serializers.UUIDField()
    data = serializers.JSONField()


class HotspotSerializer(serializers.Serializer):
    """Serializer for map hotspots returned to the frontend.

    Fields are returned with Spanish keys to match frontend expectations.
    """
    latitud_centro = serializers.FloatField()
    longitud_centro = serializers.FloatField()
    radio_estimado_metros = serializers.FloatField()
    total_casos = serializers.IntegerField()
    plaga_predominante = serializers.CharField()
    severity_index = serializers.FloatField()


# ── FeedbackTicket serializers ────────────────────────────────

FEEDBACK_TOPIC_CHOICES = [
    ('bug', 'Bug'),
    ('suggestion', 'Suggestion'),
    ('ai_error', 'AI Error'),
    ('other', 'Other'),
]


class FeedbackTicketCreateSerializer(serializers.Serializer):
    """Writable fields the frontend sends when creating a ticket."""
    topic = serializers.ChoiceField(choices=FEEDBACK_TOPIC_CHOICES)
    message = serializers.CharField(max_length=5000, min_length=10)


class FeedbackTicketResponseSerializer(serializers.Serializer):
    """Read-only representation returned after ticket creation."""
    id = serializers.IntegerField(read_only=True)
    user = serializers.CharField(source='user.username', read_only=True)
    topic = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class SensorDataPatchSerializer(serializers.Serializer):
    """
    Serializer para actualización parcial de SensorLog
    desde el microservicio de IA (Two-Stream Merge).
    Solo permite actualizar campos inferidos por CNN.
    """
    ph_level = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=14.0,
        allow_null=True,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided for update."
            )
        return attrs

# ---------------------------------------------------------------------------
# IoT NODE – serializer de creación
# ---------------------------------------------------------------------------
class IoTNodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = IoTNode
        fields = ('name','method')
