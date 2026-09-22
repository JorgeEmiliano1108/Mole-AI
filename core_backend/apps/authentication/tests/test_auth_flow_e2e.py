"""Flujo auth E2E a nivel API (reemplaza spec Playwright, V1/D).

register(consent)→login→metadata→refresh(jti rota)→logout→401,
más ARCO DELETE profile (anonimiza + audita). JWT reales, sin mocks.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from apps.core.models import AuditLog

User = get_user_model()


@pytest.fixture(autouse=True)
def _locmem_cache():
    # Sin Redis local, throttles/denylist degradan (issue 10); locmem aísla.
    with override_settings(CACHES={
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }):
        yield


@pytest.mark.django_db
def test_flujo_jwt_completo():
    c = APIClient()
    assert c.post("/api/v1/auth/register/", {
        "username": "e2e_flow", "password": "Segura123!",
        "email": "flow@e2e.mx", "consent": True,
    }, format="json").status_code == 201

    token = c.post("/api/v1/auth/login/", {
        "username": "e2e_flow", "password": "Segura123!",
    }, format="json").json()["token"]
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert c.get("/api/v1/auth/metadata/").status_code == 200

    new_token = c.post("/api/v1/auth/refresh/").json()["token"]
    assert new_token and new_token != token
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {new_token}")
    assert c.get("/api/v1/auth/metadata/").status_code == 200

    assert c.post("/api/v1/auth/logout/").status_code == 200
    assert c.get("/api/v1/auth/metadata/").status_code == 401


@pytest.mark.django_db
def test_arco_delete_anonimiza_y_audita():
    c = APIClient()
    c.post("/api/v1/auth/register/", {
        "username": "e2e_arco", "password": "Segura123!",
        "email": "arco@e2e.mx", "consent": True,
    }, format="json")
    token = c.post("/api/v1/auth/login/", {
        "username": "e2e_arco", "password": "Segura123!",
    }, format="json").json()["token"]
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resp = c.delete("/api/v1/auth/profile/")
    assert resp.status_code == 204, resp.content[:200]
    from django.contrib.auth import get_user_model as _gum

    # La fila se anonimiza y luego se borra (SET_NULL preserva datos
    # científicos); o bien queda inactiva según backend. Ambas válidas:
    gone = not _gum().objects.filter(username="e2e_arco").exists()
    assert gone
    assert AuditLog.objects.filter(action="DELETE_ACCOUNT_ARCO").exists()
    # Token huérfano (usuario inexistente/inactivo) → 401.
    assert c.get("/api/v1/auth/metadata/").status_code == 401
