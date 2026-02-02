from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

class PlantType:
    CHILE = "chile"
    MAIZ = "maiz" 
    AGUACATE = "aguacate"
    TOMATE = "tomate"
    ENDemICA_MEXICANA = "endemica_mexicana"
    DESCONOCIDA = "desconocida"

class AnalysisType:
    INFRARED = "infrared"
    RGB = "rgb"

class HealthStatus:
    HEALTHY = "healthy"
    STRESS_WATER = "stress_water"
    PEST_DETECTION = "pest_detection"
    NUTRIENT_DEFICIENCY = "nutrient_deficiency"
    MULTIPLE_ISSUES = "multiple_issues"

class ImageAnalysis:
    def __init__(
        self,
        image_id: str,
        analysis_type: str,
        plant_type: str,
        health_status: str,
        confidence: float,
        detections: List[Dict[str, Any]],
        recommendations: List[str],
        processed_at: Optional[datetime] = None
    ):
        self.image_id = image_id
        self.analysis_type = analysis_type
        self.plant_type = plant_type
        self.health_status = health_status
        self.confidence = confidence
        self.detections = detections
        self.recommendations = recommendations
        self.processed_at = processed_at or datetime.now()
        self.from_cache = False  # Atributo para tracking de cache
    
    @classmethod
    def generate_id(cls, image_bytes: bytes) -> str:
        return f"img_{hashlib.md5(image_bytes).hexdigest()[:16]}"

class VectorDocument:
    def __init__(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None,
        created_at: Optional[datetime] = None
    ):
        self.doc_id = doc_id
        self.content = content
        self.metadata = metadata
        self.embedding = embedding
        self.created_at = created_at or datetime.now()