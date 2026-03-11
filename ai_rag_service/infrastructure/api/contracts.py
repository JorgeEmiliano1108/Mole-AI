"""
API Contracts - Pydantic models for request/response validation
(VERSION FUSIONADA: Incluye MoleAIChatRequest + Vision + Diagnóstico)
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# ==========================================
# 1. EMBEDDING CONTRACTS
# ==========================================
class EmbeddingRequest(BaseModel):
    """Request model for text embedding generation"""
    text: str = Field(..., min_length=1, max_length=8000, description="Text to convert to vector")
    model: Optional[str] = Field(None, description="Model to use (optional, uses default)")   

class EmbeddingResponse(BaseModel):
    """Response model for embedding generation"""
    vector: List[float] = Field(..., description="768-dimensional embedding vector")
    dimension: int = Field(..., description="Vector dimension (should be 768)")
    model_used: str = Field(..., description="Model used for generation")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")

# ==========================================
# 2. SENSOR DATA CONTRACTS
# ==========================================
class SensorDataRequest(BaseModel):
    """Environmental sensor data for agriculture - Mole-AI Enhanced"""
    # Environmental sensors
    temperature: Optional[float] = Field(None, ge=-50.0, le=60.0, description="Temperature in Celsius")
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0, description="Humidity percentage (0-100%)")
    uv_index: Optional[float] = Field(None, ge=0.0, le=15.0, description="UV index")
    
    # Soil sensors
    soil_humidity: Optional[float] = Field(None, ge=0.0, le=100.0, description="Soil moisture percentage (0-100%)")
    ph_level: Optional[float] = Field(None, ge=0.0, le=14.0, description="Soil pH level (0-14 scale)")
    
    # Additional metadata
    device_id: Optional[str] = Field(None, description="Sensor device identifier")
    plant_id: Optional[str] = Field(None, description="Plant identifier for context")
    location: Optional[Dict[str, Any]] = Field(None, description="GPS coordinates {x, y, z}")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of sensor reading")      

# ==========================================
# 3. CHAT CONTRACTS (STANDARD)
# ==========================================
class ChatRequest(BaseModel):
    """Request model for chat generation"""
    query: str = Field(..., min_length=1, max_length=2000, description="Question or prompt")  
    context: Optional[List[str]] = Field(None, description="Context passages for RAG")        
    sensor_data: Optional[SensorDataRequest] = Field(None, description="Environmental sensor data")
    model: Optional[str] = Field(None, description="Model to use (optional, uses default)")   
    max_tokens: Optional[int] = Field(512, ge=1, le=2048, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Generation temperature")

class ChatResponse(BaseModel):
    """Response model for chat generation"""
    answer: str = Field(..., description="Generated response")
    model_used: str = Field(..., description="Model used for generation")
    tokens_generated: Optional[int] = Field(None, description="Number of tokens generated")   
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")

# ==========================================
# 4. MOLE-AI SPECIFIC CONTRACTS (LO QUE FALTABA) 🚨
# ==========================================
class MoleAIChatRequest(BaseModel):
    """Enhanced chat request for Mole-AI agricultural intelligence"""
    query: str = Field(..., min_length=1, max_length=2000, description="Agricultural question or problem")
    context: Optional[List[str]] = Field(None, description="Context passages for RAG")        
    sensor_data: Optional[SensorDataRequest] = Field(None, description="Environmental sensor readings")
    model: Optional[str] = Field(None, description="Model to use (optional, uses default)")   
    max_tokens: Optional[int] = Field(1024, ge=1, le=2048, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Generation temperature")
    image: Optional[str] = Field(None, description="Base64 encoded image or URL for multimodal context")

class MoleAIChatResponse(BaseModel):
    """Enhanced response for Mole-AI with agricultural intelligence"""
    answer: str = Field(..., description="Generated agricultural response with tactical alerts")
    model_used: str = Field(..., description="Model used for generation")
    tokens_generated: Optional[int] = Field(None, description="Number of tokens generated")   
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    tactical_alerts_count: Optional[int] = Field(None, description="Number of tactical alerts generated")

# ==========================================
# 5. VISION & DIAGNOSIS CONTRACTS
# ==========================================
class VisionAnalysisRequest(BaseModel):
    """Request for image analysis/diagnosis"""
    image: str = Field(..., description="Base64 encoded image string or URL")
    query: Optional[str] = Field(None, description="Specific question about the image (optional)")
    plant_id: Optional[str] = Field(None, description="ID of the plant being analyzed")
    sensor_data: Optional[SensorDataRequest] = Field(None, description="Contextual sensor data")

class VisionAnalysisResponse(BaseModel):
    """Response from vision analysis"""
    description: str = Field(..., description="AI description of the image")
    diagnosis: Optional[str] = Field(None, description="Potential disease diagnosis")
    confidence: float = Field(..., description="Confidence score (0.0 - 1.0)")
    recommendations: List[str] = Field(default_factory=list, description="Actionable advice")
    model_used: str = Field(..., description="Vision model used")
    processing_time_ms: Optional[float] = Field(None, description="Time taken")

# ==========================================
# 6. HEALTH & SYSTEM CONTRACTS
# ==========================================
class ModelStatus(BaseModel):
    """Model status information"""
    model: str = Field(..., description="Model name")
    is_loaded: bool = Field(..., description="Whether model is loaded")
    loading_time_ms: Optional[float] = Field(None, description="Time taken to load model")    
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")

class HealthResponse(BaseModel):
    """Health check response"""
    is_healthy: bool = Field(..., description="Overall service health")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    version: str = Field(..., description="Service version")
    models_status: List[ModelStatus] = Field(..., description="Status of all models")

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error description")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class APIInfo(BaseModel):
    """API information response"""
    name: str = Field(..., description="Service name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="Service description")
    endpoints: Dict[str, Any] = Field(..., description="Available endpoints")


# ==========================================
# 8. PH EXPLAINABILITY CONTRACTS
# ==========================================
class PhExplainRequest(BaseModel):
    """Request for pH CNN explainability analysis"""
    ph_cnn: float = Field(..., ge=0.0, le=14.0, description="pH value from TFLite CNN inference")
    plant_id: UUID = Field(..., description="Plant UUID identifier")
    sensors: Dict[str, Any] = Field(default_factory=dict, description="ESP32 sensor telemetry")
    species_name: Optional[str] = Field(None, description="Scientific species name (e.g. Zea mays)")


class PhExplainResponse(BaseModel):
    """Response from pH explainability engine"""
    ph_raw: float = Field(..., description="Raw pH value from CNN")
    ph_status: str = Field(..., description="Classification: optimal | warning | critical")
    deviation: float = Field(..., description="Distance from optimal pH")
    reasoning: str = Field(..., description="Human-readable explanation")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    sensor_context: Dict[str, Any] = Field(default_factory=dict, description="Sensor data + alerts")
    species_used: str = Field(..., description="Species used for tolerance lookup")
    confidence: str = Field(..., description="Confidence level: high | medium | low")
    data_sources: List[str] = Field(default_factory=list, description="Data sources consulted")

# ==========================================
# 7. INGESTION CONTRACTS
# ==========================================
class IngestKnowledgeRequest(BaseModel):
    """Request to ingest knowledge/files"""
    filename: str = Field(..., description="Name of the file being ingested")
    content: Optional[bytes] = Field(None, description="File content (optional if sent as file upload)")

class IngestKnowledgeResponse(BaseModel):
    """Response for ingestion operation"""
    success: bool = Field(..., description="Operation success status")
    chunks_count: int = Field(..., description="Number of chunks created")
    message: str = Field(..., description="Result message")


# ==========================================
# 9. SIGNED UPLOAD URL CONTRACTS (Sprint 2)
# ==========================================
class UploadUrlRequest(BaseModel):
    """Request to generate a Supabase Storage signed upload URL."""
    file_name: str = Field(..., min_length=1, max_length=255, description="Target file name in bucket")
    content_type: str = Field(
        "image/jpeg",
        description="MIME type of the file to upload (image/jpeg, image/png, etc.)",
    )

class UploadUrlResponse(BaseModel):
    """Response with a pre-signed URL for client-side upload."""
    upload_url: str = Field(..., description="Pre-signed PUT/POST URL for direct upload")
    storage_path: str = Field(..., description="Path inside the bucket where the file will reside")
    expires_in: int = Field(3600, description="Seconds until the signed URL expires")


# ==========================================
# 10. DIAGNOSTIC PIPELINE CONTRACTS (Sprint 2)
# ==========================================
class CreateDiagnosticRequest(BaseModel):
    """Request to trigger the CNN diagnostic pipeline."""
    plant_id: UUID = Field(..., description="Plant UUID (must exist in user_plants)")
    storage_url: str = Field(
        ..., min_length=1,
        description="Supabase Storage URL of the already-uploaded image",
    )
    species_name: Optional[str] = Field(
        None, description="If known; otherwise CNN will detect it",
    )

class DiagnosticResultResponse(BaseModel):
    """Response from the CNN diagnostic pipeline."""
    diagnostic_id: int = Field(..., description="ID of the stored AIDiagnostic record")
    plant_id: str
    species_detected: Optional[str] = Field(None)
    ph_predicted: Optional[float] = Field(None)
    condition_name: str
    condition_description: str
    severity: str
    confidence_score: float
    recommendations: List[str] = Field(default_factory=list)
    image_url: str
    ph_explanation: Optional[Dict[str, Any]] = Field(
        None, description="Output from ExplainPhUseCase if pH was detected",
    )

# ==========================================
# 8. GUARDRAILS - OUTPUT VALIDATION
# ==========================================
from pydantic import field_validator

class GuardrailValidation(BaseModel):
    """Valida que la salida del LLM cumpla estructura esperada"""
    answer: str = Field(..., min_length=1, max_length=4096)
    has_sensitive_data: bool = Field(default=False)
    language: str = Field(default="es")
    contains_alert: bool = Field(default=False)
    
    @field_validator('answer')
    @classmethod
    def validate_answer(cls, v):
        injection_keywords = ['ignore', 'disregard', 'forget', 'new rules', 'override']
        if any(kw in v.lower() for kw in injection_keywords):
            raise ValueError("Answer contains potential instruction override")
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if v not in ['es', 'en']:
            raise ValueError("Language must be 'es' or 'en'")
        return v