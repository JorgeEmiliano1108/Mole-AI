"""
Core Security - JWT Validation (ES256 with JWKS cache or HS256 fallback)
Arquitectura Hexagonal - Capa Core
LFPDPP - Cumplimiento normativo: Hasheo de PII en logs (SHA-256)
"""
import hashlib
from typing import Optional
from abc import ABC, abstractmethod

import jwt
from fastapi import HTTPException
import structlog

from app.core.config import settings
from app.core.jwks_client import JWKSClient

logger = structlog.get_logger()


def _hash_user_id(user_id: str) -> str:
    if not user_id:
        return "anonymous"
    return hashlib.sha256(user_id.encode('utf-8')).hexdigest()


class TokenValidatorPort(ABC):
    @abstractmethod
    async def validate(self, token: str) -> dict:
        ...


class HS256Validator(TokenValidatorPort):
    def __init__(self):
        self._secret = settings.JWT_SECRET_KEY or settings.SECRET_KEY
        if not self._secret:
            logger.error("jwt_config_error", error="JWT_SECRET_KEY not configured")
        self._audience = settings.JWT_AUDIENCE
        self._leeway = settings.JWT_LEEWAY

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


class JWKSValidator(TokenValidatorPort):
    def __init__(self):
        self._client = JWKSClient(
            jwks_url=settings.JWKS_URL,
            cache_ttl=settings.JWKS_CACHE_TTL_SECONDS,
        )
        self._audience = settings.JWT_AUDIENCE
        self._leeway = settings.JWT_LEEWAY

    async def validate(self, token: str) -> dict:
        try:
            headers = jwt.get_unverified_header(token)
            kid = headers.get("kid", "")
            if not kid:
                raise HTTPException(status_code=401, detail="Missing kid in token header")
            public_key = await self._client.get_public_key(kid)
            if public_key is None:
                raise HTTPException(status_code=401, detail="Unknown key id")
            claims = jwt.decode(
                token,
                public_key,
                algorithms=[settings.JWT_ALGORITHM],
                audience=self._audience,
                options={"verify_aud": True, "verify_exp": True},
                leeway=self._leeway,
            )
            hashed_sub = _hash_user_id(claims.get("sub", ""))
            logger.info("token_validated_jwks", user_hash=hashed_sub)
            return claims
        except HTTPException:
            raise
        except jwt.ExpiredSignatureError:
            logger.warning("token_expired")
            raise HTTPException(status_code=401, detail="Token Expired")
        except jwt.InvalidTokenError as e:
            logger.error("token_validation_failed", error=str(e))
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error("jwt_interceptor_error", error=str(e))
            raise HTTPException(status_code=401, detail="Unauthorized")


_token_validator: Optional[TokenValidatorPort] = None


def get_token_validator() -> TokenValidatorPort:
    global _token_validator
    if _token_validator is None:
        if settings.JWKS_URL:
            _token_validator = JWKSValidator()
        else:
            _token_validator = HS256Validator()
    return _token_validator
