"""
Esquemas de validación - Skill 01: Pydantic para contratos entre capas.
Aqui definimos los schemas que cruzan las capas del hexágono.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum
from datetime import datetime


class SeverityLevelSchema(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConditionCategorySchema(str, Enum):
    HEALTHY = "healthy"
    DISEASE = "disease"
    NUTRIENT_DEFICIENCY = "nutrient_deficiency"
    PEST = "pest"
    ENVIRONMENTAL_STRESS = "environmental_stress"
    UNKNOWN = "unknown"


class GrowthStageSchema(str, Enum):
    PLANTULA = "plántula"
    VEGETATIVA = "vegetativa"
    FLORACION = "floración"
    FRUCTIFICACION = "fructificación"
    SENESCENCIA = "senescencia"
    UNKNOWN = "unknown"


class AfflictionTypeSchema(str, Enum):
    PEST = "pest"
    FUNGAL = "fungal"
    BACTERIAL = "bacterial"
    VIRAL = "viral"
    NUTRIENT = "nutrient"
    PHYSIOLOGICAL = "physiological"
    UNKNOWN = "unknown"


class ProgressionStageSchema(str, Enum):
    INITIAL = "initial"
    ADVANCED = "advanced"
    TERMINAL = "terminal"


class VisionInputSchema(BaseModel):
    """Schema de entrada para análisis de visión."""
    plant_id: str = Field(..., min_length=1, max_length=255)
    
    @field_validator('plant_id')
    @classmethod
    def validate_plant_id(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("plant_id no puede estar vacío")
        return v.strip()


class VisionOutputSchema(BaseModel):
    """Schema de salida para resultados de inferencia CNN."""
    species: str = Field(default="Desconocida")
    condition: str = Field(default="No identificada")
    condition_category: ConditionCategorySchema = Field(default=ConditionCategorySchema.UNKNOWN)
    severity: SeverityLevelSchema = Field(default=SeverityLevelSchema.MEDIUM)
    confidence: float = Field(..., ge=0.0, le=1.0)
    ph_predicted: Optional[float] = Field(default=None, ge=0.0, le=14.0)
    model_version: str = Field(default="1.0.0")
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError("confidence debe estar entre 0 y 1")
        return v


class DiagnosticResponseSchema(BaseModel):
    """Schema de respuesta para el endpoint de diagnósticos."""
    id: Optional[str] = None
    plant_id: str
    species: str
    condition: str
    condition_category: ConditionCategorySchema
    severity: SeverityLevelSchema
    confidence: float
    ph_predicted: Optional[float] = None
    timestamp: datetime
    disclaimer: str = Field(
        default="Aviso: Este diagnóstico es generado por inteligencia artificial. "
                "Consulte a un ingeniero agrónomo para validación profesional."
    )


class EventPayloadSchema(BaseModel):
    """Schema para payloads de eventos publicados en Redis."""
    event_type: str
    plant_id: str
    diagnostic_id: str
    condition: str
    severity: SeverityLevelSchema
    ph_predicted: Optional[float] = None
    timestamp: str


class HealthCheckSchema(BaseModel):
    """Schema para respuesta de health check."""
    status: str = Field(..., pattern="^(ok|unhealthy)$")
    checks: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PlantDiagnosisSchema(BaseModel):
    """Schema de salida v2 para diagnóstico fitosanitario completo."""
    species_common: str = Field(default="Desconocida")
    species_scientific: str = Field(default="No identificada")
    growth_stage: GrowthStageSchema = Field(default=GrowthStageSchema.UNKNOWN)
    affliction_name: str = Field(default="Ninguna")
    affliction_type: AfflictionTypeSchema = Field(default=AfflictionTypeSchema.UNKNOWN)
    causal_agent: str = Field(default="Desconocido")
    severity: SeverityLevelSchema = Field(default=SeverityLevelSchema.MEDIUM)
    progression: ProgressionStageSchema = Field(default=ProgressionStageSchema.INITIAL)
    confidence: float = Field(..., ge=0.0, le=1.0)
    immediate_actions: tuple[str, ...] = Field(default_factory=tuple)
    preventive_measures: tuple[str, ...] = Field(default_factory=tuple)
    mitigation_steps: tuple[str, ...] = Field(default_factory=tuple)
    ph_predicted: Optional[float] = Field(default=None, ge=0.0, le=14.0)
    model_version: str = Field(default="2.0.0")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class DiagnosticResponseV2Schema(BaseModel):
    """Schema de respuesta v2 para el endpoint de diagnósticos."""
    id: Optional[str] = None
    plant_id: str
    diagnosis: PlantDiagnosisSchema
    timestamp: datetime
    disclaimer: str = Field(
        default="Aviso: Este diagnóstico es generado por inteligencia artificial. "
                "Consulte a un ingeniero agrónomo para validación profesional."
    )