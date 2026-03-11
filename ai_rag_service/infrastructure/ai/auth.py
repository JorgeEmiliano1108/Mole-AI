"""Adapter: Autenticación"""

import logging
import json
from pathlib import Path
from typing import Optional
from domain.models import User, UserRole
from domain.security import AuthenticationPort

logger = logging.getLogger(__name__)


class SimpleAuthAdapter(AuthenticationPort):
    """Autenticación basada en archivo JSON"""
    
    def __init__(self, users_file: str = "storage/users.json"):
        from dotenv import load_dotenv
        load_dotenv()
        self.users_file = Path(users_file)
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_default_users()
    
    async def verify_api_key(self, api_key: str) -> Optional[User]:
        """Verifica API key"""
        try:
            if not self.users_file.exists():
                return None
            
            with open(self.users_file) as f:
                users_data = json.load(f)
            
            for username, data in users_data.items():
                if data.get("api_key") == api_key:
                    return User(
                        id=api_key,
                        username=username,
                        role=UserRole(data.get("role", "agricultor"))
                    )
            
            return None
        except Exception as e:
            logger.error(f"Error en autenticación: {str(e)}")
            return None
    
    def _initialize_default_users(self):
        """Crea usuarios por defecto si no existen, usando variables de entorno"""
        if self.users_file.exists():
            return
        import os
        admin_key = os.getenv("ADMIN_API_KEY")
        farmer_key = os.getenv("FARMER_API_KEY")
        
        if not admin_key or not farmer_key:
            logger.warning("⚠️  ADMIN_API_KEY or FARMER_API_KEY not set. Using generated keys for development.")
            import secrets
            admin_key = admin_key or f"admin_{secrets.token_hex(16)}"
            farmer_key = farmer_key or f"farmer_{secrets.token_hex(16)}"
        
        default_users = {
            "admin_user": {
                "api_key": admin_key,
                "role": "admin"
            },
            "farmer_user": {
                "api_key": farmer_key,
                "role": "agricultor"
            }
        }
        with open(self.users_file, 'w') as f:
            json.dump(default_users, f, indent=2)
        logger.info(f"✅ Usuarios por defecto creados en {self.users_file}")
        logger.info(f"   ADMIN:     api_key={admin_key}")
        logger.info(f"   AGRICULTOR: api_key={farmer_key}")
