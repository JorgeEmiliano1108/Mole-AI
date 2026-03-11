"""
Domain Service - Input Validation & Sanitization
Guarantees that sensor data and user queries are safe before reaching the LLM.

WHY THIS EXISTS:
- domain.models.SensorData is a plain dataclass with NO validation.
- Pydantic contracts only guard the API boundary; internal code paths (WebSocket,
  background tasks, tests) can bypass contracts entirely.
- Prompt Injection tokens must be stripped BEFORE the prompt is assembled.
"""
import re
import logging
from typing import List

from domain.models import SensorData

logger = logging.getLogger(__name__)

# ============================================================================
# Constants: Physical limits for sensor readings
# ============================================================================
PH_MIN, PH_MAX = 0.0, 14.0
HUMIDITY_MIN, HUMIDITY_MAX = 0.0, 100.0
TEMPERATURE_MIN, TEMPERATURE_MAX = -50.0, 60.0
UV_INDEX_MIN, UV_INDEX_MAX = 0.0, 15.0
SOIL_HUMIDITY_MIN, SOIL_HUMIDITY_MAX = 0.0, 100.0

# Dangerous prompt-injection tokens for ChatML / Phi-3.5 format
_DANGEROUS_PATTERN = re.compile(
    r"<\|(?:user|assistant|system|end|endoftext|im_start|im_end|image_\d+)\|>",
    re.IGNORECASE,
)


class ValidationError(Exception):
    """Raised when sensor data contains physically impossible values."""


class SensorValidator:
    """Validates and clamps SensorData values to physically possible ranges.

    Policy:
      - Values slightly outside range are CLAMPED and a warning is logged.
      - Values absurdly outside range (double the max) raise ValidationError.
    """

    @staticmethod
    def validate(data: SensorData) -> SensorData:
        """Return a validated copy of *data*. Original is not mutated."""
        if data is None:
            return data

        air_temperature = data.air_temperature if data.air_temperature is not None else data.temperature

        def _check(value, vmin, vmax, name):
            if value is None:
                return value
            if not isinstance(value, (int, float)):
                raise ValidationError(f"{name} must be numeric, got {type(value).__name__}")
            range_size = vmax - vmin
            tolerance = range_size * 0.1  # 10% tolerance for clamp; beyond = reject
            # Absurd values -> reject (more than 10% outside valid range)
            if value < vmin - tolerance or value > vmax + tolerance:
                raise ValidationError(
                    f"{name}={value} is physically impossible (valid: {vmin}-{vmax})"
                )
            # Slightly out of range -> clamp + warn
            if value < vmin or value > vmax:
                clamped = max(vmin, min(vmax, value))
                logger.warning(f"{name}={value} out of range, clamped to {clamped}")
                return clamped
            return value

        return SensorData(
            temperature=_check(air_temperature, TEMPERATURE_MIN, TEMPERATURE_MAX, "air_temperature"),
            air_temperature=_check(air_temperature, TEMPERATURE_MIN, TEMPERATURE_MAX, "air_temperature"),
            humidity=_check(data.humidity, HUMIDITY_MIN, HUMIDITY_MAX, "humidity"),
            uv_index=_check(data.uv_index, UV_INDEX_MIN, UV_INDEX_MAX, "uv_index"),
            soil_humidity=_check(data.soil_humidity, SOIL_HUMIDITY_MIN, SOIL_HUMIDITY_MAX, "soil_humidity"),
            ph_level=_check(data.ph_level, PH_MIN, PH_MAX, "ph_level"),
            device_id=data.device_id,
            plant_id=data.plant_id,
            location=data.location,
            timestamp=data.timestamp,
        )


class InputSanitizer:
    """Strips prompt-injection tokens and excessive whitespace from user input."""

    @staticmethod
    def sanitize_query(query: str) -> str:
        if not query:
            return query
        # Strip ChatML / Phi-3.5 special tokens
        cleaned = _DANGEROUS_PATTERN.sub("", query)
        # Collapse multiple newlines (common injection trick to push context out of view)
        cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
        if cleaned != query:
            logger.warning("Prompt-injection tokens stripped from user query")
        return cleaned.strip()

    @staticmethod
    def sanitize_context(context_items: List[str]) -> List[str]:
        """Sanitize every item in a context list."""
        if not context_items:
            return context_items
        return [InputSanitizer.sanitize_query(item) for item in context_items]
