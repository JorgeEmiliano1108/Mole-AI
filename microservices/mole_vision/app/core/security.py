"""
Core Security - Zero-Trust JWT Validation with JWKS Cache
Skill 01: Arquitectura Hexagonal - Capa Core
Skill 02: LFPDPPP - Sin almacenamiento de PII en logs
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx
import jwt
from jwt import PyJWKClient, PyJWKClientError

from fastapi import HTTPException
import structlog

logger = structlog.get_logger()


class SupabaseTokenValidator:
    """
    Validador autónomo de JWT usando JWKS de Supabase.
    
    Anti-DoS Features:
    - Cache JWKS con cooldown de 5 minutos
    - Solo refresh si el kid no existe en cache
    - Lock asíncrono para evitar tormentas de peticiones
    """
    
    def __init__(
        self,
        supabase_url: str,
        jwks_cache_ttl: int = 300,
    ):
        self.supabase_url = supabase_url.rstrip("/")
        self.jwks_url = f"{self.supabase_url}/.well-known/jwks.json"
        self._cache: Optional[dict] = None
        self._cache_timestamp: Optional[datetime] = None
        self._jwks_client: Optional[PyJWKClient] = None
        self._lock = asyncio.Lock()
        self._cooldown = timedelta(seconds=jwks_cache_ttl)
    
    async def validate(self, token: str) -> dict:
        """
        Valida el token JWT y retorna los claims.
        
        Args:
            token: JWT token string
            
        Returns:
            dict: Claims del token (sub, email, role, etc.)
            
        Raises:
            HTTPException(401): Token inválido, expirado o no autorizado
        """
        try:
            signing_key = await self._get_signing_key(token)
            
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience="authenticated",
                issuer=self.supabase_url,
                options={
                    "verify_aud": True,
                    "verify_exp": True,
                    "verify_iss": True,
                    
                },
            )
            
            logger.info("token_validated", user_id=claims.get("sub"))
            return claims
            
        except jwt.ExpiredSignatureError:
            logger.warning("token_expired")
            raise HTTPException(
                status_code=401,
                detail={"type": "https://mole.ai/errors/unauthorized", "title": "Token Expired", "status": 401},
            )
        except jwt.InvalidAudienceError:
            logger.warning("token_invalid_audience")
            raise HTTPException(
                status_code=401,
                detail={"type": "https://mole.ai/errors/unauthorized", "title": "Invalid Audience", "status": 401},
            )
        except jwt.InvalidSignatureError:
            logger.warning("token_invalid_signature")
            raise HTTPException(
                status_code=401,
                detail={"type": "https://mole.ai/errors/unauthorized", "title": "Invalid Signature", "status": 401},
            )
        except jwt.DecodeError:
            logger.warning("token_decode_error")
            raise HTTPException(
                status_code=401,
                detail={"type": "https://mole.ai/errors/unauthorized", "title": "Invalid Token", "status": 401},
            )
        except PyJWKClientError as e:
            logger.error("jwks_client_error", error=str(e))
            raise HTTPException(
                status_code=503,
                detail={"type": "https://mole.ai/errors/service_unavailable", "title": "Auth Service Unavailable", "status": 503},
            )
        except Exception as e:
            logger.exception("unexpected_token_validation_error")
            raise HTTPException(
                status_code=401,
                detail={"type": "https://mole.ai/errors/unauthorized", "title": "Token Validation Failed", "status": 401},
            )
    
    async def _get_signing_key(self, token: str) -> jwt.PyJWK:
        """
        Obtiene la clave de firma del JWKS con estrategia Anti-DoS.
        
        - Si el kid del token NO está en cache: retorna error (no hace refresh)
        - Solo hace refresh si el kid no existe Y el cooldown expiró
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
        except Exception:
            raise HTTPException(
                status_code=401,
                detail={"type": "https://mole.ai/errors/unauthorized", "title": "Invalid Token Header", "status": 401},
            )
        
        if not kid:
            raise HTTPException(
                status_code=401,
                detail={"type": "https://mole.ai/errors/unauthorized", "title": "Missing Key ID", "status": 401},
            )
        
        if self._cache and kid in self._cache:
            return self._cache[kid]
        
        async with self._lock:
            if self._cache and kid in self._cache:
                return self._cache[kid]
            
            if self._cache_timestamp:
                time_since_refresh = datetime.utcnow() - self._cache_timestamp
                if time_since_refresh < self._cooldown:
                    logger.warning("jwks_cooldown_active", kid=kid)
                    raise HTTPException(
                        status_code=401,
                        detail={"type": "https://mole.ai/errors/unauthorized", "title": "Unknown Key ID", "status": 401},
                    )
            
            logger.info("refreshing_jwks")
            try:
                self._jwks_client = PyJWKClient(self.jwks_url)
                keys = self._jwks_client.get_signing_keys()
                self._cache = {key.key_id: key for key in keys}
                self._cache_timestamp = datetime.utcnow()
            except Exception as e:
                logger.error("jwks_refresh_failed", error=str(e))
                raise HTTPException(
                    status_code=503,
                    detail={"type": "https://mole.ai/errors/service_unavailable", "title": "Auth Service Unavailable", "status": 503},
                )
            
            if kid in self._cache:
                return self._cache[kid]
            
            logger.warning("kid_not_found_after_refresh", kid=kid)
            raise HTTPException(
                status_code=401,
                detail={"type": "https://mole.ai/errors/unauthorized", "title": "Unknown Key ID", "status": 401},
            )


_token_validator: Optional[SupabaseTokenValidator] = None


def get_token_validator() -> SupabaseTokenValidator:
    """Factory para obtener la instancia del validador."""
    global _token_validator
    if _token_validator is None:
        from app.core.config import settings
        _token_validator = SupabaseTokenValidator(
            supabase_url=settings.SUPABASE_URL,
            jwks_cache_ttl=settings.JWKS_CACHE_TTL_SECONDS,
        )
    return _token_validator