"""Modelos del dominio - Vision Service"""

from dataclasses import dataclass
from typing import List
from enum import Enum


class PlantState(str, Enum):
    """Estados posibles de una planta"""
    SANA = "Sana"
    ATENCION = "Atención"
    PELIGRO = "Peligro"


@dataclass
class VisionAnalysisRequest:
    """Solicitud de análisis visual"""
    image_base64: str


@dataclass
class PlantSymptom:
    """Síntoma identificado en la planta"""
    nombre: str
    confianza: float
    descripcion: str


@dataclass
class VisionAnalysisResult:
    """Resultado del análisis visual"""
    estado: PlantState
    confianza: float
    sintomas: List[PlantSymptom]
    especie_probable: str
    análisis_visual: str
