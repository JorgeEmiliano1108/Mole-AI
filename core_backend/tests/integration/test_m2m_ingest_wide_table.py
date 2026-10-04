# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""Ingesta M2M wide-table → esquema 1:N (A3 FREEZE: sensor_logs, solo lectura)."""
import uuid
from typing import Any, cast

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import AmbientReading, HardwareBinding, SoilReading
from apps.plants.models import UserPlant


def _setup_bound_plant():
    User = get_user_model()
    user = User.objects.create_user(username=f'u-{uuid.uuid4().hex[:8]}', password='x')
    plant = UserPlant.objects.create(user=user, nickname='P')
    from apps.core.models import Device
    device = Device.objects.create(
        owner=user, name='d', auth_token=f'tok-{uuid.uuid4().hex[:8]}')
    binding = HardwareBinding.objects.create(
        device=device, hardware_pin='32', plant=plant)
    return plant, binding


@pytest.mark.django_db
@override_settings(HARDWARE_API_KEY="test-hw-key")
def test_sensor_data_m2m_success_flat_payload_creates_rows():
    client = APIClient()
    plant, binding = _setup_bound_plant()
    payload = {
        "plant_id": str(plant.id),
        "recorded_at": timezone.now().isoformat(),
        "soil_humidity": 61.2,
        "air_temperature": 28.4,
        "uv_index": 5.5,
        "light_level": 410.0,
        "ph_level": 6.4,
    }
    response = cast(Any, client.post(
        "/api/v1/sensor-data/", data=payload, format="json",
        HTTP_X_HARDWARE_API_KEY="test-hw-key",
    ))
    assert response.status_code == 201
    assert response.data["status"] == "success"
    assert response.data["registered"] == 1
    soil = SoilReading.objects.get(binding=binding)
    assert soil.soil_humidity == 61.2
    assert soil.ph_level == 6.4
    ambient = AmbientReading.objects.get(device=binding.device)
    assert ambient.air_temperature == 28.4


@pytest.mark.django_db
@override_settings(HARDWARE_API_KEY="test-hw-key")
def test_sensor_data_m2m_rejects_missing_api_key():
    client = APIClient()
    response = cast(Any, client.post("/api/v1/sensor-data/",
                                     data={"plant_id": str(uuid.uuid4()),
                                           "air_temperature": 25.0},
                                     format="json"))
    assert response.status_code == 401


@pytest.mark.django_db
@override_settings(HARDWARE_API_KEY="test-hw-key")
def test_sensor_data_m2m_rejects_missing_plant_id():
    client = APIClient()
    response = cast(Any, client.post(
        "/api/v1/sensor-data/", data={"air_temperature": 25.0},
        format="json", HTTP_X_HARDWARE_API_KEY="test-hw-key",
    ))
    assert response.status_code == 400
    assert "details" in response.data
    assert "plant_id" in response.data["details"]


@pytest.mark.django_db
@override_settings(HARDWARE_API_KEY="test-hw-key")
def test_sensor_data_m2m_unbound_plant_404():
    client = APIClient()
    User = get_user_model()
    user = User.objects.create_user(username='orphan', password='x')
    orphan = UserPlant.objects.create(user=user, nickname='O')
    response = cast(Any, client.post(
        "/api/v1/sensor-data/",
        data={"plant_id": str(orphan.id), "air_temperature": 24.8},
        format="json", HTTP_X_HARDWARE_API_KEY="test-hw-key",
    ))
    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(HARDWARE_API_KEY="test-hw-key")
def test_sensor_batch_m2m_bulk_insert_success():
    client = APIClient()
    plant1, _ = _setup_bound_plant()
    plant2, _ = _setup_bound_plant()
    payload = {
        "batch": [
            {"plant_id": str(plant1.id), "air_temperature": 26.1, "soil_humidity": 60.0},
            {"plant_id": str(plant2.id), "air_temperature": 27.0,
             "soil_humidity": 59.4, "ph_level": 6.8},
            {"plant_id": str(uuid.uuid4()), "air_temperature": 20.0,
             "soil_humidity": 50.0},
        ]
    }
    response = cast(Any, client.post(
        "/api/v1/sensor-data/batch/", data=payload, format="json",
        HTTP_X_HARDWARE_API_KEY="test-hw-key",
    ))
    assert response.status_code == 201
    assert response.data["registered"] == 2
    assert len(response.data["skipped_unbound_plants"]) == 1
    assert SoilReading.objects.count() == 2
    assert AmbientReading.objects.count() == 2
