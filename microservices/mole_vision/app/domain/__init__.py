"""
Domain Layer - Entidades y Esquemas
Skill 01: Capa pura sin dependencias externas.
"""
from app.domain.entities import (
    DiagnosticResult,
    DiagnosticEvent,
    SeverityLevel,
    ConditionCategory,
    PlantDiagnosis,
    GrowthStage,
    AfflictionType,
    ProgressionStage,
)
from app.domain.schemas import (
    VisionInputSchema,
    VisionOutputSchema,
    DiagnosticResponseSchema,
    DiagnosticResponseV2Schema,
    PlantDiagnosisSchema,
    EventPayloadSchema,
    HealthCheckSchema,
)

__all__ = [
    # Entities
    "DiagnosticResult",
    "DiagnosticEvent",
    "SeverityLevel",
    "ConditionCategory",
    "PlantDiagnosis",
    "GrowthStage",
    "AfflictionType",
    "ProgressionStage",
    # Schemas
    "VisionInputSchema",
    "VisionOutputSchema",
    "DiagnosticResponseSchema",
    "DiagnosticResponseV2Schema",
    "PlantDiagnosisSchema",
    "EventPayloadSchema",
    "HealthCheckSchema",
]