"""
Core Security - Local JWT Validation 
Arquitectura Hexagonal - Capa Core
LFPDPP - Cumplimiento normativo: Hasheo de PII en logs (SHA-256)
"""
import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException
import structlog

from app.core.config import settings

logger = structlog.get_logger()


def _hash_user_id(user_id: str) -> str:
    """Aplica pseudo-anonimización (SHA-256) al UUID para cumplir con LFPDPPP."""
    if not user_id:
        return "anonymous"
    return hashlib.sha256(user_id.encode('utf-8')).hexdigest()


class LocalTokenValidator:
    """Validador simétrico estricto usando JWT_SECRET_KEY local (HS256)."""

    def __init__(self):
        self._secret = getattr(settings, 'JWT_SECRET_KEY', None) or getattr(settings, 'SECRET_KEY', None)
        if not self._secret:
            logger.error("jwt_config_error", error="JWT_SECRET_KEY not configured")
        self._audience = getattr(settings, 'JWT_AUDIENCE', 'authenticated')
        self._leeway = getattr(settings, 'JWT_LEEWAY', 30)

    async def validate(self, token: str) -> dict:
        if not self._secret:
            raise HTTPException(status_code=401, detail="Auth configuration error")

        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=["HS256"],
                audience=self._audience,
                options={"verify_aud": True, "verify_exp": True},
                leeway=self._leeway,
            )
            hashed_sub = _hash_user_id(claims.get("sub", ""))
            logger.info("token_validated", user_hash=hashed_sub)
            return claims

        except jwt.ExpiredSignatureError:
            logger.warning("token_expired")
            raise HTTPException(status_code=401, detail="Token Expired")
        except jwt.InvalidTokenError as e:
            logger.error("token_validation_failed", error=str(e))
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error("jwt_interceptor_error", error=str(e))
            raise HTTPException(status_code=401, detail="Unauthorized")


_token_validator: Optional[LocalTokenValidator] = None


def get_token_validator() -> LocalTokenValidator:
    """Singleton para el validador local."""
    global _token_validator
    if _token_validator is None:
        _token_validator = LocalTokenValidator()
    return _token_validator
