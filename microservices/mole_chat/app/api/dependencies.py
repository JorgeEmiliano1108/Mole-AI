"""
API Dependencies - Inyección de Seguridad Zero-Trust
ETSI EN 303 645: API-Key per device, JWT per user.
"""
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import get_token_validator
from app.core.config import settings
import structlog

logger = structlog.get_logger()
security_scheme = HTTPBearer()


async def verify_api_key(x_api_key: str = Header(default="", alias="X-API-KEY")) -> str:
    """Validate device-level API key (ETSI EN 303 645 compliance)."""
    if not settings.API_KEY:
        # If API_KEY is not configured, skip validation (backward compat)
        return "default-device"
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Falta X-API-KEY")
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="API Key inválida")
    return "authenticated-device"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    _device: str = Depends(verify_api_key),
) -> str:
    """Valida el JWT (ES256 via JWKS o HS256 local) y retorna el UUID del usuario autenticado."""
    try:
        validator = get_token_validator()
        claims = await validator.validate(credentials.credentials)
        user_id = claims.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido: falta claim 'sub'")
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error("jwt_interceptor_error", error=str(e))
        raise HTTPException(status_code=401, detail="No autorizado")