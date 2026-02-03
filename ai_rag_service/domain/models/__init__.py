"""Modelos del dominio - RAG Service"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RAGChunk:
    """Chunk de conocimiento recuperado"""
    contenido: str
    fuente: str
    confianza: float


@dataclass
class VisionOutput:
    """Output del servicio de visión (input para RAG)"""
    estado: str
    confianza: float
    especie_probable: str
    sintomas: List[str]
    análisis_visual: str


@dataclass
class SensorData:
    """Datos de sensores"""
    ph: float
    humedad: float
    temp: float
    uv: float


@dataclass
class DiagnoseRequest:
    """Solicitud de diagnóstico (RAG + Phi-3.5)"""
    vision_output: VisionOutput
    sensores: SensorData


@dataclass
class FinalDiagnosis:
    """Diagnóstico final después de RAG + Phi-3.5"""
    diagnostico: str
    recomendaciones: List[str]
    fuentes_consultadas: List[str]
    confianza_final: float
    requiere_accion_humana: bool


# ============================================================================
# SEGURIDAD Y CONTROL DE ACCESO
# ============================================================================

from enum import Enum

class UserRole(str, Enum):
    """Roles en el sistema"""
    ADMIN = "admin"
    AGRICULTOR = "agricultor"


@dataclass
class User:
    """Usuario autenticado"""
    username: str
    api_key: str
    role: UserRole
    
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    @property
    def is_agricultor(self) -> bool:
        return self.role == UserRole.AGRICULTOR


@dataclass
class AuditLog:
    """Registro de auditoría"""
    usuario: str
    accion: str
    recurso: str
    timestamp: str
    resultado: str
    detalles: str


@dataclass
class PublicSource:
    """Fuente de conocimiento público"""
    nombre: str  # GBIF, Tropicos, USDA, Wikidata
    url_base: str
    tipo: str  # "api", "dataset"
    ultima_sincronizacion: Optional[str] = None
    registro_count: int = 0
