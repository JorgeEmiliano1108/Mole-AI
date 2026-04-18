"""
Puerto de Visión - Skill 01: Interfaz abstracta para inferencia CNN.
La implementación concreta (TFLite) vivirá en infrastructure/adapters/.
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities import DiagnosticResult


class VisionClientPort(ABC):
    """
    Puerto abstracto para el cliente de inferencia de visión.
    
    Contract: El caso de uso llama a analyze() sin conocer la implementación.
    Los bytes de imagen deben estar libre de metadatos EXIF/GPS (Skill 02).
    """
    
    @abstractmethod
    async def analyze(self, image_bytes: bytes) -> "DiagnosticResult":
        """
        Ejecuta la inferencia CNN sobre la imagen.
        
        Args:
            image_bytes: Bytes de imagen limpia (sin EXIF/GPS).
            
        Returns:
            DiagnosticResult: Entidad de dominio con el diagnóstico.
        """
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        """Verifica si el modelo está cargado y listo."""
        pass