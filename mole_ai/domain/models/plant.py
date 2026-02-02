from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PlantState(str, Enum):
    SANA = "Sana"
    ATENCION = "Atención"
    PELIGRO = "Peligro"


class SensorData(BaseModel):
    """Datos de sensores del ambiente de la planta"""
    ph: float = Field(..., ge=0, le=14, description="pH del suelo")
    humedad: float = Field(..., ge=0, le=100, description="Humedad relativa (%)")
    temp: float = Field(..., ge=-50, le=60, description="Temperatura ambiente (°C)")
    uv: float = Field(..., ge=0, le=15, description="Índice UV")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    plant_id: Optional[str] = None

    @validator('ph')
    def validate_ph_range(cls, v):
        if not 4.0 <= v <= 9.0:
            raise ValueError('pH fuera de rango agrícola típico (4.0-9.0)')
        return v

    @validator('humedad')
    def validate_humidity_range(cls, v):
        if not 10.0 <= v <= 100.0:
            raise ValueError('Humedad fuera de rango real (10-100%)')
        return v


class PlantImage(BaseModel):
    """Imagen de planta con metadatos"""
    image_base64: str = Field(..., description="Imagen en formato base64")
    filename: Optional[str] = None
    format: str = Field(default="jpeg", description="Formato de imagen")
    size_bytes: Optional[int] = None
    captured_at: Optional[datetime] = Field(default_factory=datetime.now)
    plant_id: Optional[str] = None


class VisualAnalysis(BaseModel):
    """Resultado del análisis visual de la planta"""
    estado: PlantState
    confianza: float = Field(..., ge=0, le=1)
    especie_probable: Optional[str] = None
    sintomas_visibles: List[str] = Field(default_factory=list)
    areas_afectadas: List[str] = Field(default_factory=list)
    severidad_visual: Optional[float] = Field(None, ge=0, le=1)


class KnowledgeContext(BaseModel):
    """Contexto de conocimiento agronómico recuperado"""
    documentos: List[str] = Field(default_factory=list)
    fuentes: List[str] = Field(default_factory=list)
    scores_relevancia: List[float] = Field(default_factory=list)
    tema_principal: Optional[str] = None


class PlantDiagnosis(BaseModel):
    """Diagnóstico completo de planta"""
    
    # Identificación
    id: Optional[str] = None
    plant_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Datos de entrada
    imagen: PlantImage
    sensores: SensorData
    conocimiento: Optional[KnowledgeContext] = None
    
    # Resultado del diagnóstico
    estado: PlantState
    confianza: float = Field(..., ge=0, le=1)
    especie: Optional[str] = None
    sintomas: List[str] = Field(default_factory=list)
    diagnostico: str = Field(..., description="Diagnóstico técnico detallado")
    recomendaciones: List[str] = Field(default_factory=list)
    fuentes: List[str] = Field(default_factory=list)
    
    # Metadatos del análisis
    modelo_utilizado: str = Field(..., description="Modelo de IA utilizado")
    tiempo_inferencia: Optional[float] = None  # en segundos
    requiere_accion_humana: bool = Field(default=False)
    
    @validator('confianza')
    def validate_confidence_threshold(cls, v):
        if v < 0.3:
            raise ValueError('Confianza mínima requerida: 0.3')
        return v
    
    @property
    def es_confiable(self) -> bool:
        """Determina si el diagnóstico es confiable"""
        return self.confianza >= 0.85
    
    @property
    def nivel_riesgo(self) -> str:
        """Retorna nivel de riesgo basado en estado y confianza"""
        if self.estado == PlantState.PELIGRO and self.es_confiable:
            return "ALTO"
        elif self.estado == PlantState.ATENCION or not self.es_confiable:
            return "MEDIO"
        else:
            return "BAJO"


class DiagnosticFilter(BaseModel):
    """Filtros para búsqueda de diagnósticos"""
    plant_id: Optional[str] = None
    estado: Optional[PlantState] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    especie: Optional[str] = None
    confianza_minima: Optional[float] = Field(None, ge=0, le=1)


class AlertConfig(BaseModel):
    """Configuración de alertas automáticas"""
    plant_id: str
    umbrales: Dict[str, float] = Field(default_factory=dict)
    estados_alerta: List[PlantState] = Field(default_factory=lambda: [PlantState.PELIGRO])
    confianza_minima_alerta: float = Field(default=0.7, ge=0, le=1)
    recipients: List[str] = Field(default_factory=list)
    activa: bool = Field(default=True)


class SystemMetrics(BaseModel):
    """Métricas del sistema"""
    total_diagnosticos: int = 0
    diagnosticos_hoy: int = 0
    promedio_confianza: float = 0.0
    plantas_activas: int = 0
    modelo_actual: str = ""
    uptime_segundos: int = 0