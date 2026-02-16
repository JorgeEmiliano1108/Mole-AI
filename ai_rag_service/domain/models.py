"""
Domain Models - Pure business entities without infrastructure dependencies
(VERSION OMEGA: Con DiagnoseRequest, VisionOutput, User y RAGChunk)
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

# ==========================================
# 1. ENUMS (Roles y Tipos)
# ==========================================

class UserRole(str, Enum):
    """User roles definition"""
    ADMIN = "admin"
    USER = "user"
    AGRICULTOR = "agricultor"
    SYSTEM = "system"

class ModelType(str, Enum):
    """Available AI models"""
    SENTENCE_TRANSFORMER = "sentence-transformers/all-mpnet-base-v2"
    PHI35_VISION = "microsoft/Phi-3.5-vision-instruct"

# ==========================================
# 2. ENTIDADES PRINCIPALES (Usuario y Sensores)
# ==========================================

@dataclass
class User:
    """User entity definition"""
    id: str
    username: str
    email: Optional[str] = None
    role: UserRole = UserRole.USER

@dataclass
class SensorData:
    """Environmental sensor data for agriculture"""
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    uv_index: Optional[float] = None
    soil_humidity: Optional[float] = None
    ph_level: Optional[float] = None
    device_id: Optional[str] = None
    plant_id: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

# ==========================================
# 3. ENTIDADES RAG (Búsqueda Vectorial)
# ==========================================

@dataclass
class RAGChunk:
    """Represents a chunk of text/knowledge for retrieval"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None
    vector: Optional[List[float]] = None

# ==========================================
# 4. ENTIDADES DE VISIÓN Y DIAGNÓSTICO (¡TODO JUNTO!) 👁️🩺
# ==========================================

@dataclass
class VisionOutput:
    """Structured output from Vision Models"""
    description: str
    confidence: float
    tags: List[str] = field(default_factory=list)
    detected_objects: List[Dict[str, Any]] = field(default_factory=list)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DiagnoseRequest:
    """Request for Plant Disease Diagnosis"""
    image: str  # Base64 string or URL
    plant_id: Optional[str] = None
    region: Optional[str] = None
    description: Optional[str] = None
    user: Optional[User] = None
    vision_output: Optional['VisionOutput'] = None
    sensor_data: Optional['SensorData'] = None

@dataclass
class DiagnoseResponse:
    """Response for Plant Diagnosis"""
    diagnosis: str
    confidence: float
    recommendations: List[str] = field(default_factory=list)
    vision_output: Optional[VisionOutput] = None
    processing_time_ms: Optional[float] = None

@dataclass
class FinalDiagnosis:
    """Final diagnosis output from reasoning model"""
    diagnosis: str
    recommendations: List[str] = field(default_factory=list)
    sources_consulted: List[Dict[str, Any]] = field(default_factory=list)
    final_confidence: float = 0.0
    requires_human_action: bool = False

# ==========================================
# 5. MODELOS DE CHAT E IA
# ==========================================

@dataclass
class ChatRequest:
    """Request for LLM generation"""
    query: str
    context: List[str] = field(default_factory=list)
    model: ModelType = ModelType.PHI35_VISION
    max_tokens: int = 512
    temperature: float = 0.7
    sensor_data: Optional[SensorData] = None
    image: Optional[str] = None
    user: Optional[User] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = []

@dataclass
class ChatResponse:
    """Response from LLM generation"""
    answer: str
    model_used: str
    tokens_generated: Optional[int] = None
    processing_time_ms: Optional[float] = None

# ==========================================
# 6. MODELOS DE EMBEDDINGS
# ==========================================

@dataclass
class EmbeddingRequest:
    """Request for text embedding generation"""
    text: str
    model: ModelType = ModelType.SENTENCE_TRANSFORMER

@dataclass
class EmbeddingResponse:
    """Response containing embedding vector"""
    vector: List[float]
    dimension: int
    model_used: str
    processing_time_ms: Optional[float] = None

# ==========================================
# 7. SALUD DEL SISTEMA
# ==========================================

@dataclass
class ModelStatus:
    """Status of AI models"""
    model: str
    is_loaded: bool
    loading_time_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None

@dataclass
class ServiceHealth:
    """Overall service health status"""
    is_healthy: bool
    models_status: List[ModelStatus]
    uptime_seconds: float
    version: str