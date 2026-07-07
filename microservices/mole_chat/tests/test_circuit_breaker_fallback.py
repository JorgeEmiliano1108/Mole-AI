import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from app.infrastructure.adapters.nvidia_client import LLMClient

def test_circuit_breaker_fallback(monkeypatch):
    """Synchronous wrapper that runs the async LLMClient."""
    import asyncio
    """El cliente debe abrir el circuit breaker tras 3 fallos consecutivos y devolver
    una respuesta de fallback en llamadas posteriores."""

    async def always_fail(_messages):
        raise Exception("simulated failure")

    client = LLMClient()
    # Parchear el método interno que llama a la API
    monkeypatch.setattr(client, "_raw_generate", always_fail)

    # Tres llamadas que provocan fallo -> breaker pasa a OPEN
    asyncio.run(client.generate("sys", "msg"))
    asyncio.run(client.generate("sys", "msg"))
    asyncio.run(client.generate("sys", "msg"))

    # El breaker debe estar abierto
    assert client.breaker.state == "OPEN"

    # Cuarta llamada debe devolver el fallback sin intentar la API
    resp = asyncio.run(client.generate("sys", "msg"))
    assert "congestión" in resp.respuesta.lower()
