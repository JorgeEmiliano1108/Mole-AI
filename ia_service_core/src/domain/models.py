from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Entidad para representar un fragmento de conocimiento agrícola
class Documento(BaseModel):
    contenido: str
    fuente: str
    pagina: Optional[int] = None
    vector: Optional[List[float]] = None

# Entidad para mensajes del chat
class Mensaje(BaseModel):
    rol: str
    contenido: str

# Entidad para análisis de visión de plantas
class AnalisisVision(BaseModel):
    imagen_id: str
    tipo_planta: Optional[str] = None
    diagnostico: str
    recomendaciones: List[str]
    confianza: float
    fecha_analisis: datetime = datetime.now()

# Entidad para datos de sensores agrícolas
class DatosSensores(BaseModel):
    humedad: Optional[float] = None
    temperatura: Optional[float] = None
    ph: Optional[float] = None
    uv: Optional[float] = None
    fecha_medicion: datetime = datetime.now()

# Entidad para análisis basado en sensores
class AnalisisSensores(BaseModel):
    datos: DatosSensores
    diagnostico: str
    recomendaciones: List[str]
    estado_salud: str
    alertas: List[str]