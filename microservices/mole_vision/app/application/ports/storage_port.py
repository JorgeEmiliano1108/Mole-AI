"""
Puerto de Repositorio - Skill 01: Interfaz abstracta para persistencia.
Skill 03: Debe ser async para no bloquear el Event Loop.
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities import DiagnosticResult


class DiagnosticRepositoryPort(ABC):
    """
    Puerto abstracto para persistencia de diagnósticos.
    
    Contract: El caso de uso guarda diagnósticos sin conocer el storage.
    Implementaciones: Supabase, PostgreSQL, MongoDB, etc.
    """
    
    @abstractmethod
    async def save_diagnostic(self, diagnostic: "DiagnosticResult") -> str:
        """
        Persiste un diagnóstico y retorna su ID.
        
        Args:
            diagnostic: Entidad de dominio con el diagnóstico.
            
        Returns:
            str: ID único del diagnóstico persisted.
        """
        pass
    
    @abstractmethod
    async def get_diagnostic(self, diagnostic_id: str) -> "DiagnosticResult":
        """
        Recupera un diagnóstico por su ID.
        
        Args:
            diagnostic_id: ID único del diagnóstico.
            
        Returns:
            DiagnosticResult: Entidad de dominio recuperada.
            
        Raises:
            DiagnosticNotFoundError: Si no existe el diagnóstico.
        """
        pass
    
    @abstractmethod
    async def is_healthy(self) -> bool:
        """Verifica la conexión con el repositorio."""
        pass