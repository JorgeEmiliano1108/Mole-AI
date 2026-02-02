from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import uuid

class SensorData:
    """Datos de sensores del ESP32"""
    def __init__(
        self,
        device_id: str,
        timestamp: datetime,
        humidity: float,
        temperature: float,
        ph: float,
        uv_index: float,
        soil_moisture: float,
        plant_id: Optional[str] = None
    ):
        self.device_id = device_id
        self.timestamp = timestamp
        self.humidity = humidity
        self.temperature = temperature
        self.ph = ph
        self.uv_index = uv_index
        self.soil_moisture = soil_moisture
        self.plant_id = plant_id or f"plant_{device_id}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat(),
            "humidity": self.humidity,
            "temperature": self.temperature,
            "ph": self.ph,
            "uv_index": self.uv_index,
            "soil_moisture": self.soil_moisture,
            "plant_id": self.plant_id
        }

class PlantDiagnosis:
    """Diagnóstico completo de la planta"""
    def __init__(
        self,
        plant_id: str,
        sensor_data: SensorData,
        vision_analysis: Optional[Dict[str, Any]],
        rag_context: List[str],
        diagnosis: str,
        treatment_plan: List[str],
        urgency_level: str,  # low, medium, high, critical
        confidence: float,
        recommendations: List[str],
        created_at: Optional[datetime] = None
    ):
        self.diagnosis_id = f"diag_{uuid.uuid4().hex[:12]}"
        self.plant_id = plant_id
        self.sensor_data = sensor_data
        self.vision_analysis = vision_analysis
        self.rag_context = rag_context
        self.diagnosis = diagnosis
        self.treatment_plan = treatment_plan
        self.urgency_level = urgency_level
        self.confidence = confidence
        self.recommendations = recommendations
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "diagnosis_id": self.diagnosis_id,
            "plant_id": self.plant_id,
            "sensor_data": self.sensor_data.to_dict(),
            "vision_analysis": self.vision_analysis,
            "rag_context": self.rag_context,
            "diagnosis": self.diagnosis,
            "treatment_plan": self.treatment_plan,
            "urgency_level": self.urgency_level,
            "confidence": self.confidence,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat()
        }

class KnowledgeDocument:
    """Documento para base de conocimiento"""
    def __init__(
        self,
        content: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        created_at: Optional[datetime] = None
    ):
        self.doc_id = doc_id or f"doc_{uuid.uuid4().hex[:12]}"
        self.content = content
        self.metadata = metadata
        self.embedding = embedding
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat()
        }

class LLMResponse:
    """Respuesta del servicio de LLM"""
    def __init__(
        self,
        content: str,
        model_used: str,
        tokens_used: int,
        processing_time: float,
        success: bool,
        error_message: Optional[str] = None,
        context_used: Optional[List[str]] = None
    ):
        self.content = content
        self.model_used = model_used
        self.tokens_used = tokens_used
        self.processing_time = processing_time
        self.success = success
        self.error_message = error_message
        self.context_used = context_used or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "processing_time": self.processing_time,
            "success": self.success,
            "error_message": self.error_message,
            "context_used": self.context_used
        }

class HealthStatus:
    HEALTHY = "healthy"
    STRESS_WATER = "stress_water"
    PEST_DETECTION = "pest_detection"
    NUTRIENT_DEFICIENCY = "nutrient_deficiency"
    MULTIPLE_ISSUES = "multiple_issues"

class UrgencyLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"