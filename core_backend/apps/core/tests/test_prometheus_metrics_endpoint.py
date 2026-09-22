import pytest
from django.urls import resolve
from django.urls.exceptions import Resolver404
from rest_framework.test import APIClient

def test_health_endpoint_ok():
    # NOTA: /metrics/ no existe (django-prometheus no instalado);
    # el healthcheck canónico es /health/ (mole_ai_backend/urls.py).
    client = APIClient()
    response = client.get('/health/')
    assert response.status_code == 200
    assert response.content == b'OK'

def test_metrics_endpoint_absent_documents_gap():
    # Documenta el gap a nivel URLconf (determinista en cualquier
    # DEBUG/plantilla): ninguna ruta sirve /metrics/.
    # Si se instala django-prometheus a futuro, este test debe
    # reescribirse a GET /metrics/ → 200 + process_cpu_seconds_total.
    with pytest.raises(Resolver404):
        resolve('/metrics/')
