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
"""
Domain entities for Core module.

Contains the core business entities without infrastructure dependencies.
These are pure Python objects that represent the business concepts.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class SeverityLevel(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class DiagnosticType(Enum):
    DISEASE = 'disease'
    NUTRIENT_DEFICIENCY = 'nutrient_deficiency'
    PEST_INFESTATION = 'pest_infestation'
    ENVIRONMENTAL_STRESS = 'environmental_stress'
    GROWTH_ANALYSIS = 'growth_analysis'


@dataclass
class SensorReading:
    """Pure domain entity for a Wide-Table sensor row."""
    plant_id: str
    soil_humidity: Optional[float] = None
    air_temperature: Optional[float] = None
    uv_index: Optional[float] = None
    light_level: Optional[float] = None
    ph_level: Optional[float] = None
    recorded_at: Optional[datetime] = None

    def is_critical(self) -> bool:
        """Check if any reading indicates critical conditions."""
        if self.air_temperature is not None and (self.air_temperature > 35 or self.air_temperature < 5):
            return True
        if self.soil_humidity is not None and (self.soil_humidity < 10 or self.soil_humidity > 90):
            return True
        if self.ph_level is not None and (self.ph_level < 4.0 or self.ph_level > 9.0):
            return True
        return False


@dataclass
class PlantKnowledge:
    """Pure domain entity for plant knowledge."""
    title: str
    content: str
    plant_species: str
    plant_genus: str
    plant_family: str
    common_names: List[str]
    source: Optional[str] = None
    confidence_score: float = 0.0
    
    def is_reliable(self) -> bool:
        """Check if knowledge source is reliable."""
        return self.confidence_score >= 0.7


@dataclass
class DiagnosticRecommendation:
    """Pure domain entity for diagnostic recommendations."""
    action: str
    priority: str
    timeline: str
    resources_needed: List[str]


@dataclass
class PlantDiagnostic:
    """Pure domain entity for plant diagnostics."""
    plant_id: str
    diagnostic_type: DiagnosticType
    condition_name: str
    condition_description: str
    severity: SeverityLevel
    ai_model_used: str
    confidence_score: float
    recommendations: List[DiagnosticRecommendation]
    treatment_protocol: str
    follow_up_required: bool = False
    follow_up_days: Optional[int] = None
    
    def requires_immediate_action(self) -> bool:
        """Check if diagnostic requires immediate attention."""
        return self.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]
    
    def get_priority_recommendations(self) -> List[DiagnosticRecommendation]:
        """Get high-priority recommendations."""
        return [r for r in self.recommendations if r.priority == 'high']