"""Servicios de seguridad - Domain layer"""

from abc import ABC, abstractmethod
from typing import Optional
from ..models import User, UserRole


class AuthenticationPort(ABC):
    """Puerto para autenticación"""
    
    @abstractmethod
    async def verify_api_key(self, api_key: str) -> Optional[User]:
        """Verifica API key y retorna usuario o None"""


class AuditPort(ABC):
    """Puerto para auditoría"""
    
    @abstractmethod
    async def log_action(self, usuario: str, accion: str, recurso: str, 
                        resultado: str, detalles: str) -> None:
        """Registra acción de usuario"""


def require_role(allowed_roles: list[UserRole]):
    """Validador de rol para use cases"""
    def validator(user: User) -> bool:
        return user.role in allowed_roles
    return validator
