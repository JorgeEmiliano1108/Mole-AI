from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Diagnostic:
    id: Optional[int]
    plant_id: str
    species: Optional[str]
    condition: Optional[str]
    severity: Optional[str]
    ph_predicted: Optional[float]
    timestamp: str
    raw: Optional[Dict[str, Any]] = None


@dataclass
class VisionOutput:
    species: Optional[str]
    condition: Optional[str]
    severity: Optional[str]
    ph_predicted: Optional[float]
    confidence: Optional[float]
