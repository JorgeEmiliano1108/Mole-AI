import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.api.dependencies import get_current_user

client = TestClient(app)

def test_health_check_is_public():
    """El health check debe ser accesible sin token."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "mole_chat"}

def test_chat_endpoint_without_token_is_rejected():
    """Si no se envía el header Authorization, debe dar 403 Forbidden."""
    payload = {"user_id": "user-123", "message": "Hola"}
    response = client.post("/api/v1/mole-ai/chat", json=payload)
    assert response.status_code == 403  # FastAPI lanza 403 cuando falta el Bearer token

def test_chat_endpoint_identity_mismatch():
    """Si el token es de Juan, pero intenta consultar los datos de Pedro, debe fallar."""
    
    # Hacemos un "Override" de la dependencia para simular un token válido de "usuario_A"
    app.dependency_overrides[get_current_user] = lambda: "usuario_A"
    
    # Pero el request pide procesar cosas de "usuario_B" (Intento de suplantación)
    payload = {"user_id": "usuario_B", "message": "Hola"}
    response = client.post("/api/v1/mole-ai/chat", json=payload)
    
    assert response.status_code == 403
    assert "no coincide con la firma del token" in response.json()["detail"]
    
    # Limpiamos el override
    app.dependency_overrides.clear()