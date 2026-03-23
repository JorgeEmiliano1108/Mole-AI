"""Tests para PATCH /api/v1/sensor-data/<id>/ (Two-Stream Merge)."""
import uuid

import pytest
from rest_framework.test import APIClient

from apps.core.infrastructure.repositories.models import SensorLog


HARDWARE_API_KEY = "test-hardware-key-for-ci"


@pytest.fixture(autouse=True)
def _patch_hw_key(settings):
    settings.HARDWARE_API_KEY = HARDWARE_API_KEY


@pytest.fixture
def hw_client():
    client = APIClient()
    client.credentials(HTTP_X_HARDWARE_API_KEY=HARDWARE_API_KEY)
    return client


@pytest.fixture
def sensor_log(db):
    return SensorLog.objects.create(
        plant_id=uuid.uuid4(),
        soil_humidity=45.0,
        air_temperature=22.0,
        ph_level=None,
    )


@pytest.mark.django_db
class TestSensorDataPatch:
    """Two-Stream Merge endpoint tests."""

    def test_patch_ph_level_success(self, hw_client, sensor_log):
        """AI microservice can inject pH after CNN inference."""
        url = f"/api/v1/sensor-data/{sensor_log.pk}/"
        response = hw_client.patch(url, {"ph_level": 6.3}, format="json")

        assert response.status_code == 200
        assert response.data["status"] == "updated"
        assert response.data["sensor_log_id"] == sensor_log.pk

        sensor_log.refresh_from_db()
        assert sensor_log.ph_level == pytest.approx(6.3)

    def test_patch_ph_out_of_range(self, hw_client, sensor_log):
        """pH must be in [0.0, 14.0]."""
        url = f"/api/v1/sensor-data/{sensor_log.pk}/"
        response = hw_client.patch(url, {"ph_level": 15.0}, format="json")
        assert response.status_code == 400

    def test_patch_empty_body_rejected(self, hw_client, sensor_log):
        """Empty body must be rejected."""
        url = f"/api/v1/sensor-data/{sensor_log.pk}/"
        response = hw_client.patch(url, {}, format="json")
        assert response.status_code == 400

    def test_patch_nonexistent_log(self, hw_client, db):
        """404 for non-existent SensorLog."""
        response = hw_client.patch(
            "/api/v1/sensor-data/999999/",
            {"ph_level": 7.0},
            format="json",
        )
        assert response.status_code == 404

    def test_patch_without_api_key_rejected(self, sensor_log):
        """Unauthenticated request rejected."""
        client = APIClient()
        url = f"/api/v1/sensor-data/{sensor_log.pk}/"
        response = client.patch(url, {"ph_level": 6.0}, format="json")
        assert response.status_code in (401, 403)

    def test_patch_idempotent(self, hw_client, sensor_log):
        """Patching same field twice produces last-write-wins."""
        url = f"/api/v1/sensor-data/{sensor_log.pk}/"
        hw_client.patch(url, {"ph_level": 6.3}, format="json")
        response = hw_client.patch(url, {"ph_level": 6.5}, format="json")

        assert response.status_code == 200
        sensor_log.refresh_from_db()
        assert sensor_log.ph_level == pytest.approx(6.5)
