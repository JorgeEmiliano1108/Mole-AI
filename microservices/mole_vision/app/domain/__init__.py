"""
Domain Layer - Entidades y Esquemas
Skill 01: Capa pura sin dependencias externas.
"""
from app.domain.entities import (
    DiagnosticResult,
    PhEstimation,
    DiagnosticEvent,
    SeverityLevel,
    ConditionCategory,
)
from app.domain.schemas import (
    VisionInputSchema,
    VisionOutputSchema,
    DiagnosticResponseSchema,
    PhStripResponseSchema,
    EventPayloadSchema,
    HealthCheckSchema,
)

__all__ = [
    # Entities
    "DiagnosticResult",
    "PhEstimation",
    "DiagnosticEvent",
    "SeverityLevel",
    "ConditionCategory",
    # Schemas
    "VisionInputSchema",
    "VisionOutputSchema",
    "DiagnosticResponseSchema",
    "PhStripResponseSchema",
    "EventPayloadSchema",
    "HealthCheckSchema",
]