"""Seguridad ingesta edge (S09/REC-1): permiso Bearer por dispositivo + rotación.

- Sin token → 401 (ya no AllowAny).
- Token revocado (is_active=False) → 401.
- Token expirado → 401.
- Rotación (owner): 200 + token nuevo distinto, viejo invalidado, con expiración.
- Rotación ajena (no owner, no staff) → 403.
"""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import Device

User = get_user_model()


@pytest.fixture(autouse=True)
def _locmem_cache(settings):
    """Throttles sin Redis: cache en memoria (en compose hay redis real)."""
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }


@pytest.fixture
def owner(db):
    return User.objects.create_user(username="owner1", email="o1@mole.ai", password="x")


@pytest.fixture
def device(db, owner):
    return Device.objects.create(
        owner=owner, name="esp32-1", auth_token="tok-original-123", status="offline"
    )


def _edge_post(token=None, payload=None):
    client = APIClient()
    if token:
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client.post(
        "/api/v1/sensor-data/edge-batch/",
        payload or {"ts": 9999999999, "ri": 5},
        format="json",
    )


@pytest.mark.django_db
def test_edge_sin_token_401(device):
    assert _edge_post().status_code == 401


@pytest.mark.django_db
def test_edge_token_invalido_401(device):
    assert _edge_post(token="no-existe").status_code == 401


@pytest.mark.django_db
def test_edge_token_revocado_401(device):
    device.is_active = False
    device.save(update_fields=["is_active"])
    assert _edge_post(token="tok-original-123").status_code == 401


@pytest.mark.django_db
def test_edge_token_expirado_401(device):
    device.auth_token_expires_at = timezone.now() - timedelta(seconds=1)
    device.save(update_fields=["auth_token_expires_at"])
    assert _edge_post(token="tok-original-123").status_code == 401


@pytest.mark.django_db
def test_rotate_owner_ok_e_invalida_viejo(db, owner, device):
    client = APIClient()
    client.force_authenticate(user=owner)
    resp = client.post(f"/api/v1/devices/{device.id}/rotate/")
    assert resp.status_code == 200
    new_token = resp.json()["auth_token"]
    assert new_token != "tok-original-123"
    assert resp.json()["expires_at"] is not None
    # Viejo invalidado, nuevo aceptado por el permiso (400 = pasa auth, falla payload mínimo)
    assert _edge_post(token="tok-original-123").status_code == 401
    assert _edge_post(token=new_token).status_code in (200, 400)


@pytest.mark.django_db
def test_rotate_tercero_403(db, owner, device):
    otro = User.objects.create_user(username="otro", email="otro@mole.ai", password="x")
    client = APIClient()
    client.force_authenticate(user=otro)
    resp = client.post(f"/api/v1/devices/{device.id}/rotate/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_rotate_inexistente_404(db, owner):
    import uuid
    client = APIClient()
    client.force_authenticate(user=owner)
    resp = client.post(f"/api/v1/devices/{uuid.uuid4()}/rotate/")
    assert resp.status_code == 404
