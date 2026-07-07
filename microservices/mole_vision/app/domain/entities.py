"""
Entidades de dominio puras - Skill 01: Sin dependencias de infraestructura.
Usa @dataclass estándar de Python, sin Pydantic, FastAPI ni librerías externas.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from enum import Enum


class SeverityLevel(str, Enum):
    """Niveles de severidad para diagnósticos."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConditionCategory(str, Enum):
    """Categorías de condición de la planta."""
    HEALTHY = "healthy"
    DISEASE = "disease"
    NUTRIENT_DEFICIENCY = "nutrient_deficiency"
    PEST = "pest"
    ENVIRONMENTAL_STRESS = "environmental_stress"
    UNKNOWN = "unknown"


class GrowthStage(str, Enum):
    """Etapa de crecimiento de la planta."""
    PLANTULA = "plántula"
    VEGETATIVA = "vegetativa"
    FLORACION = "floración"
    FRUCTIFICACION = "fructificación"
    SENESCENCIA = "senescencia"
    UNKNOWN = "unknown"


class AfflictionType(str, Enum):
    """Tipo de aflicción que afecta a la planta."""
    PEST = "pest"
    FUNGAL = "fungal"
    BACTERIAL = "bacterial"
    VIRAL = "viral"
    NUTRIENT = "nutrient"
    PHYSIOLOGICAL = "physiological"
    UNKNOWN = "unknown"


class ProgressionStage(str, Enum):
    """Etapa de progresión de la aflicción."""
    INITIAL = "initial"
    ADVANCED = "advanced"
    TERMINAL = "terminal"


@dataclass(frozen=True)
class DiagnosticResult:
    """
    Entidad de dominio puro para el resultado de un diagnóstico.
    Representa el núcleo del negocio sin dependencias externas.
    """
    plant_id: str
    species: str
    condition: str
    condition_category: ConditionCategory
    severity: SeverityLevel
    confidence: float
    ph_predicted: Optional[float] = None
    timestamp: Optional [datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', datetime.now(timezone.utc).replace(tzinfo=None))
    
    @property
    def is_critical(self) -> bool:
        return self.severity == SeverityLevel.CRITICAL
    
    @property
    def requires_immediate_action(self) -> bool:
        return self.is_critical or self.severity == SeverityLevel.HIGH


@dataclass(frozen=True)
class DiagnosticEvent:
    """
    Entidad de dominio para eventos publicados en Redis.
    Representa el payload del evento de diagnóstico completado.
    """
    event_type: str
    plant_id: str
    diagnostic_id: str
    condition: str
    severity: SeverityLevel
    ph_predicted: Optional[float]
    timestamp: str
    
    def to_payload(self) -> dict:
        """Serialización para el broker de eventos."""
        return {
            "event_type": self.event_type,
            "plant_id": self.plant_id,
            "diagnostic_id": self.diagnostic_id,
            "condition": self.condition,
            "severity": self.severity.value,
            "ph_predicted": self.ph_predicted,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class PlantDiagnosis:
    """
    Entidad de dominio para diagnóstico fitosanitario completo con detección
    de plagas/enfermedades, etapa de crecimiento y recomendaciones.
    """
    # -- Identificación --
    plant_id: str
    species_common: str
    species_scientific: str

    # -- Etapa de crecimiento --
    growth_stage: GrowthStage

    # -- Plaga / Enfermedad --
    affliction_name: str
    affliction_type: AfflictionType
    causal_agent: str

    # -- Severidad y progresión --
    severity: SeverityLevel
    progression: ProgressionStage
    confidence: float

    # -- Recomendaciones --
    immediate_actions: tuple[str, ...]
    preventive_measures: tuple[str, ...]
    mitigation_steps: tuple[str, ...]

    # -- Metadatos --
    ph_predicted: Optional[float] = None
    timestamp: Optional[datetime] = None
    model_version: str = "2.0.0"

    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).replace(tzinfo=None))
        object.__setattr__(self, "confidence", max(0.0, min(1.0, self.confidence)))

    @property
    def requires_immediate_action(self) -> bool:
        return self.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL) \
            or self.progression == ProgressionStage.TERMINAL