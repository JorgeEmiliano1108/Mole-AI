"""Domain Services: Enhanced Authentication with Rate Limiting

TODO: HEXAGONAL VIOLATION — EnhancedAuthAdapter is an ADAPTER that should live
in infrastructure/ai/enhanced_auth.py, not in domain/services/. This was left
in place to avoid breaking imports. Move to infrastructure in a future refactor.
"""

import logging
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from domain.models import UserRole
from domain.ports import AuthenticationPort

logger = logging.getLogger(__name__)


class EnhancedUser:
    """Usuario mejorado con metadata extendida"""
    
    def __init__(self, username: str, role: UserRole, api_key: str, **kwargs):
        self.username = username
        self.role = role
        self.api_key = api_key
        self.farm_id = kwargs.get('farm_id')
        self.permissions = kwargs.get('permissions', [])
        self.rate_limit = kwargs.get('rate_limit', 100)
        self.created_at = kwargs.get('created_at', datetime.now())
        self.last_used = kwargs.get('last_used')
        self.expires_at = kwargs.get('expires_at')
        self.metadata = kwargs.get('metadata', {})
    
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions or self.is_admin
    
    def to_dict(self) -> Dict:
        """Convierte usuario a dict para cache/storage"""
        return {
            "username": self.username,
            "role": self.role.value if hasattr(self.role, 'value') else str(self.role),
            "api_key": self.api_key,
            "farm_id": self.farm_id,
            "permissions": self.permissions,
            "rate_limit": self.rate_limit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata
        }


class RateLimiter:
    """Limitador de tasa configurable"""
    
    def __init__(self, requests_per_minute: int = 100, redis_client=None):
        self.requests_per_minute = requests_per_minute
        self.redis = redis_client
        self.requests_cache = {} if not redis_client else None
        
    async def acquire(self, api_key: str) -> bool:
        """
        Intenta adquirir un permiso de rate limiting
        
        Args:
            api_key: API key para limitar
            
        Returns:
            True si se permite la request, False si excede el límite
        """
        current_minute = int(time.time() // 60)
        key = f"rate_limit:{api_key}:{current_minute}"
        
        if self.redis:
            return await self._redis_acquire(api_key, current_minute)
        else:
            return await self._memory_acquire(key)
    
    async def _redis_acquire(self, api_key: str, current_minute: int) -> bool:
        """Rate limiting con Redis"""
        try:
            current_count = await self.redis.incr(key)
            if current_count == 1:
                await self.redis.expire(key, 60)  # Expira en 1 minuto
            
            user_limit = await self._get_user_limit(api_key)
            return current_count <= user_limit
            
        except Exception as e:
            logger.error(f"❌ Redis rate limiting error: {str(e)}")
            return True  # Graceful degradation
    
    async def _memory_acquire(self, key: str) -> bool:
        """Rate limiting en memoria (fallback)"""
        current_time = time.time()
        
        # Limpiar cache viejo
        self.requests_cache = {
            k: v for k, v in self.requests_cache.items()
            if current_time - k < 60  # Mantener solo último minuto
        }
        
        current_count = self.requests_cache.get(key, 0) + 1
        self.requests_cache[key] = current_time
        
        # Extraer límite de usuario (default 100)
        api_key_from_key = key.split(":")[1].split(":")[0]
        user_limit = await self._get_user_limit(api_key_from_key)
        
        return current_count <= user_limit
    
    async def _get_user_limit(self, api_key: str) -> int:
        """Obtiene límite personalizado del usuario"""
        # TODO: Implementar consulta a base de datos de usuarios
        # Por ahora, retornar default basado en rol
        if api_key == "admin_key_12345":
            return 200  # Admin tiene límite mayor
        else:
            return 100  # Default


class EnhancedAuthAdapter(AuthenticationPort):
    """Adaptador de autenticación mejorado con rate limiting y persistencia"""
    
    def __init__(self, users_file: str = "storage/users.json", redis_client=None):
        self.users_file = Path(users_file)
        self.redis = redis_client
        self.rate_limiter = RateLimiter(redis_client=redis_client)
        
    async def initialize(self):
        """Inicializa el adaptador creando usuarios por defecto si no existen"""
        await self._ensure_default_users()
    
    async def verify_api_key(self, api_key: str, request_info: Optional[Dict] = None) -> Optional[EnhancedUser]:
        """
        Verifica API key con rate limiting y validación completa
        
        Args:
            api_key: API key a verificar
            request_info: Información adicional de la request (IP, user agent, etc.)
            
        Returns:
            EnhancedUser si válido, None si inválido
        """
        try:
            # 1. Rate limiting primero (rápido)
            if not await self.rate_limiter.acquire(api_key):
                logger.warning(f"🚫 Rate limit exceeded for API key: {api_key[:10]}...")
                raise RateLimitException("Rate limit exceeded. Please try again later.")
            
            # 2. Verificar en cache Redis si está disponible
            user = await self._get_cached_user(api_key)
            if user:
                await self._update_last_used(api_key)
                return user
            
            # 3. Verificar en base de datos
            user = await self._get_user_from_db(api_key)
            if user:
                await self._cache_user(api_key, user)
                await self._update_last_used(api_key)
                
                # Log de acceso exitoso
                logger.info(f"✅ API key verified: {user.username} ({user.role.value})")
                return user
            
            # 4. Log de fallo
            logger.warning(f"❌ Invalid API key attempted: {api_key[:10]}...")
            return None
            
        except RateLimitException:
            raise  # Re-throw
        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}")
            return None
    
    async def _ensure_default_users(self):
        """Crea usuarios por defecto si no existen"""
        if not self.users_file.exists():
            default_users = {
                "admin_key_12345": {
                    "username": "admin",
                    "role": "admin",
                    "farm_id": "demo_farm",
                    "permissions": ["rag.query", "rag.upload", "admin.all"],
                    "rate_limit": 200,
                    "created_at": datetime.now().isoformat(),
                    "metadata": {
                        "device_type": "api_key",
                        "description": "Default admin user"
                    }
                },
                "farmer_key_67890": {
                    "username": "farmer",
                    "role": "agricultor",
                    "farm_id": "demo_farm",
                    "permissions": ["rag.query"],
                    "rate_limit": 100,
                    "created_at": datetime.now().isoformat(),
                    "metadata": {
                        "device_type": "api_key",
                        "description": "Default farmer user"
                    }
                }
            }
            
            self.users_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(default_users, f, indent=2)
            
            logger.info("✅ Default users created with enhanced authentication")
            logger.info(f"   ADMIN: api_key=admin_key_12345 (limit: 200 req/min)")
            logger.info(f"   AGRICULTOR: api_key=farmer_key_67890 (limit: 100 req/min)")
    
    async def _get_cached_user(self, api_key: str) -> Optional[EnhancedUser]:
        """Obtiene usuario desde cache Redis"""
        if not self.redis:
            return None
        
        try:
            cached_data = await self.redis.get(f"user:{api_key}")
            if cached_data:
                user_dict = json.loads(cached_data)
                return self._dict_to_enhanced_user(user_dict)
        except Exception as e:
            logger.error(f"❌ Cache error: {str(e)}")
        
        return None
    
    async def _cache_user(self, api_key: str, user: EnhancedUser, ttl: int = 300):
        """Cachea usuario en Redis"""
        if not self.redis:
            return
        
        try:
            await self.redis.setex(
                f"user:{api_key}",
                ttl,
                json.dumps(user.to_dict())
            )
        except Exception as e:
            logger.error(f"❌ Cache error: {str(e)}")
    
    async def _get_user_from_db(self, api_key: str) -> Optional[EnhancedUser]:
        """Obtiene usuario desde base de datos (JSON file)"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            user_data = users_data.get(api_key)
            if user_data:
                return self._dict_to_enhanced_user(user_data)
                
        except FileNotFoundError:
            logger.warning(f"⚠️ Users file not found: {self.users_file}")
        except Exception as e:
            logger.error(f"❌ Error reading users file: {str(e)}")
        
        return None
    
    def _dict_to_enhanced_user(self, user_data: Dict) -> EnhancedUser:
        """Convierte dict a EnhancedUser"""
        role = UserRole.ADMIN if user_data.get("role") == "admin" else UserRole.AGRICULTOR
        
        created_at = None
        if user_data.get("created_at"):
            created_at = datetime.fromisoformat(user_data["created_at"])
        
        last_used = None
        if user_data.get("last_used"):
            last_used = datetime.fromisoformat(user_data["last_used"])
        
        expires_at = None
        if user_data.get("expires_at"):
            expires_at = datetime.fromisoformat(user_data["expires_at"])
        
        return EnhancedUser(
            username=user_data.get("username", "unknown"),
            role=role,
            api_key=user_data.get("api_key", ""),
            farm_id=user_data.get("farm_id"),
            permissions=user_data.get("permissions", []),
            rate_limit=user_data.get("rate_limit", 100),
            created_at=created_at,
            last_used=last_used,
            expires_at=expires_at,
            metadata=user_data.get("metadata", {})
        )
    
    async def _update_last_used(self, api_key: str):
        """Actualiza timestamp de último uso"""
        try:
            # Actualizar en cache
            if self.redis:
                cached_data = await self.redis.get(f"user:{api_key}")
                if cached_data:
                    user_dict = json.loads(cached_data)
                    user_dict["last_used"] = datetime.now().isoformat()
                    await self.redis.setex(
                        f"user:{api_key}",
                        300,  # 5 minutos TTL
                        json.dumps(user_dict)
                    )
            
            # Actualizar en archivo (persistente)
            user_data = await self._get_user_from_db(api_key)
            if user_data:
                await self._update_user_in_file(api_key, {"last_used": datetime.now().isoformat()})
                
        except Exception as e:
            logger.error(f"❌ Error updating last_used: {str(e)}")
    
    async def _update_user_in_file(self, api_key: str, updates: Dict):
        """Actualiza información de usuario en archivo"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            if api_key in users_data:
                users_data[api_key].update(updates)
                
                with open(self.users_file, 'w', encoding='utf-8') as f:
                    json.dump(users_data, f, indent=2)
                    
        except Exception as e:
            logger.error(f"❌ Error updating user file: {str(e)}")
    
    async def create_user(self, user_data: Dict) -> Optional[EnhancedUser]:
        """Crea nuevo usuario"""
        api_key = user_data.get("api_key")
        if not api_key:
            return None
        
        try:
            # Verificar que no exista
            existing_user = await self._get_user_from_db(api_key)
            if existing_user:
                return None
            
            # Agregar nuevo usuario
            user_data["created_at"] = datetime.now().isoformat()
            user_data["last_used"] = None
            
            await self._update_user_in_file(api_key, user_data)
            
            # Cachear nuevo usuario
            user = self._dict_to_enhanced_user(user_data)
            await self._cache_user(api_key, user)
            
            logger.info(f"✅ New user created: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"❌ Error creating user: {str(e)}")
            return None
    
    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoca una API key"""
        try:
            # Eliminar de cache
            if self.redis:
                await self.redis.delete(f"user:{api_key}")
            
            # Eliminar de archivo
            with open(self.users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            if api_key in users_data:
                del users_data[api_key]
                
                with open(self.users_file, 'w', encoding='utf-8') as f:
                    json.dump(users_data, f, indent=2)
                
                logger.info(f"🗑️ API key revoked: {api_key[:10]}...")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error revoking API key: {str(e)}")
        
        return False
    
    async def list_users(self) -> List[Dict]:
        """Lista todos los usuarios (admin only)"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            user_list = []
            for api_key, user_data in users_data.items():
                user_info = user_data.copy()
                user_info["api_key_preview"] = f"{api_key[:8]}..."
                user_list.append(user_info)
            
            return user_list
            
        except Exception as e:
            logger.error(f"❌ Error listing users: {str(e)}")
            return []


class RateLimitException(Exception):
    """Excepción para rate limiting"""
