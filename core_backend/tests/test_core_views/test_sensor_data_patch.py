"""Tests para PATCH /api/v1/sensor-data/<id>/ — archivo congelado (A3 FREEZE)."""
import pytest
from rest_framework.test import APIClient


HARDWARE_API_KEY = "test-hardware-key-for-ci"


@pytest.fixture(autouse=True)
def _patch_hw_key(settings):
    settings.HARDWARE_API_KEY = HARDWARE_API_KEY


@pytest.fixture
def hw_client():
    client = APIClient()
    client.credentials(HTTP_X_HARDWARE_API_KEY=HARDWARE_API_KEY)
    return client


@pytest.mark.django_db
class TestSensorDataPatchFrozen:
    """sensor_logs es archivo de solo lectura: todo PATCH responde 410 Gone."""

    def test_patch_returns_410(self, hw_client):
        response = hw_client.patch(
            "/api/v1/sensor-data/999999/",
            {"ph_level": 6.3},
            format="json",
        )
        assert response.status_code == 410

    def test_patch_without_api_key_rejected(self):
        client = APIClient()
        response = client.patch("/api/v1/sensor-data/1/", {"ph_level": 6.0}, format="json")
        assert response.status_code in (401, 403, 410)
