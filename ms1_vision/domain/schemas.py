from typing import Optional
from pydantic import BaseModel, ConfigDict


class VisionOutputModel(BaseModel):
    model_config = ConfigDict()
    species: Optional[str] = None
    condition: Optional[str] = None
    severity: Optional[str] = None
    ph_predicted: Optional[float] = None
    confidence: Optional[float] = None
    pred_idx: Optional[int] = None


class DiagnosticModel(BaseModel):
    model_config = ConfigDict()
    id: Optional[int] = None
    plant_id: str
    species: Optional[str] = None
    condition: Optional[str] = None
    severity: Optional[str] = None
    ph_predicted: Optional[float] = None
    timestamp: str
    raw: Optional[VisionOutputModel] = None
