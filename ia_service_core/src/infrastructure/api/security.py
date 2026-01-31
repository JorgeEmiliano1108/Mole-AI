import os 
from fastapi import Security, HTTPException, status 
from fastapi.security import APIKeyHeader

API_KEY_HEADER _APIKeyHeader(name="X-Internal-Service-Key", auto_error=False)

INTERAL_KEY = os.getenv("microAI")

async def verify_internal_key(api_key: str = Security(API_KEY_HEADER)):
    """
    Verifica que la petición venga del sys django auth
    """
    if api_key != INTERNAL_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso Denegado"
        )
    return api_key
