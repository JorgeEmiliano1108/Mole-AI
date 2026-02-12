"""
Domain entities for Core module.

Contains the core business entities without infrastructure dependencies.
These are pure Python objects that represent the business concepts.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class SensorType(Enum):
    TEMPERATURE = 'temperature'
    HUMIDITY = 'humidity'
    LIGHT = 'light'
    SOIL_MOISTURE = 'soil_moisture'
    PH = 'ph'
    NUTRIENTS = 'nutrients'


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
    """Pure domain entity for sensor readings."""
    device_id: str
    sensor_type: SensorType
    value: float
    unit: str
    plant_id: Optional[str] = None
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    location_z: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    def is_critical(self) -> bool:
        """Check if reading indicates critical conditions."""
        if self.sensor_type == SensorType.TEMPERATURE:
            return self.value > 35 or self.value < 5
        elif self.sensor_type == SensorType.HUMIDITY:
            return self.value < 20 or self.value > 90
        elif self.sensor_type == SensorType.SOIL_MOISTURE:
            return self.value < 10
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