"""
API Dependencies - Inyección de Seguridad Zero-Trust
"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import get_token_validator
import structlog

logger = structlog.get_logger()
security_scheme = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:
    """Valida el JWT y retorna el UUID del usuario autenticado."""
    try:
        validator = get_token_validator()
        # Se ejecuta la validación matemática ES256 y descarga de JWKS
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