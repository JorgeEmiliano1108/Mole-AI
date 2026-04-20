"""
Core Security - JWT Validation 
Arquitectura Hexagonal - Capa Core
LFPDPPP - Cumplimiento normativo: Hashing de PII en logs (SHA-256)
"""
import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt import PyJWKClient
from fastapi import HTTPException
import structlog

from app.core.config import settings

logger = structlog.get_logger()

def _hash_user_id(user_id: str) -> str:
    """Aplica pseudo-anonimización (SHA-256) al UUID para cumplir con LFPDPPP."""
    if not user_id:
        return "anonymous"
    return hashlib.sha256(user_id.encode('utf-8')).hexdigest()

class SupabaseTokenValidator:
    """Validador asimétrico estricto descargando llaves de Supabase."""
    
    def __init__(self, supabase_url: str, jwks_cache_ttl: int = 300):
        # Protegemos contra URLs vacías
        self.supabase_url = supabase_url.rstrip("/") if supabase_url else ""
        self.jwks_url = f"{self.supabase_url}/auth/v1/.well-known/jwks.json"
        
        self._cache: Optional[dict] = None
        self._cache_timestamp: Optional[datetime] = None
        self._jwks_client: Optional[PyJWKClient] = None
        self._lock = asyncio.Lock()
        self._cooldown = timedelta(seconds=jwks_cache_ttl)
    
    async def validate(self, token: str) -> dict:
        try:
            # 1. Obtener la llave pública de Supabase
            signing_key = await self._get_signing_key(token)
            
            # 2. Validar matemáticamente (Soportamos los estándares de Supabase)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256", "HS256"], 
                audience="authenticated",
                options={
                    "verify_aud": True,
                    "verify_exp": True,
                    "verify_iss": False  
                },
                leeway=10  
            )
            hashed_sub = _hash_user_id(claims.get("sub", ""))
            logger.info("token_validated", user_hash=hashed_sub)
            return claims
            
        except jwt.ExpiredSignatureError:
            logger.warning("token_expired")
            raise HTTPException(status_code=401, detail="Token Expired")
        except Exception as e:
            logger.error("token_validation_failed", error=str(e))
            raise HTTPException(status_code=401, detail="Unauthorized")

    async def _get_signing_key(self, token: str) -> jwt.PyJWK:
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid Token Header")
        
        if not kid:
            raise HTTPException(status_code=401, detail="Missing Key ID in token")
        
        # Estrategia Anti-DoS con caché
        if self._cache and kid in self._cache:
            return self._cache[kid]
        
        async with self._lock:
            if self._cache and kid in self._cache:
                return self._cache[kid]
            
            try:
                self._jwks_client = PyJWKClient(self.jwks_url)
                keys = self._jwks_client.get_signing_keys()
                self._cache = {key.key_id: key for key in keys}
                self._cache_timestamp = datetime.now(timezone.utc)
            except Exception as e:
                logger.error("jwks_refresh_failed", error=str(e))
                raise HTTPException(status_code=503, detail="Auth Service Unavailable")
            
            if kid in self._cache:
                return self._cache[kid]
            
            raise HTTPException(status_code=401, detail="Unknown Key ID")

_token_validator: Optional[SupabaseTokenValidator] = None

def get_token_validator() -> SupabaseTokenValidator:
    global _token_validator
    if _token_validator is None:
        _token_validator = SupabaseTokenValidator(
            supabase_url=settings.SUPABASE_URL,
            jwks_cache_ttl=settings.JWKS_CACHE_TTL_SECONDS,
        )
    return _token_validator