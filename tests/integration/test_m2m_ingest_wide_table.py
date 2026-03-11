import uuid
from typing import Any, cast
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.mark.django_db
@override_settings(HARDWARE_API_KEY="test-hw-key")
def test_sensor_data_m2m_success_flat_payload_creates_single_row():
    client = APIClient()
    plant_id = str(uuid.uuid4())
    recorded_at = timezone.now().isoformat()

    payload = {
        "plant_id": plant_id,
        "recorded_at": recorded_at,
        "soil_humidity": 61.2,
        "air_temperature": 28.4,
        "uv_index": 5.5,
        "light_level": 410.0,
        "ph_level": 6.4,
    }

    with patch("core.presentation.views.UserPlant.objects") as plant_qs, \
         patch("core.presentation.views.SensorLog.objects.create") as create_mock:
        plant_qs.filter.return_value.exists.return_value = True
        response = cast(Any, client.post(
            "/api/v1/sensor-data/",
            data=payload,
            format="json",
            HTTP_X_HARDWARE_API_KEY="test-hw-key",
        ))

    assert response.status_code == 201
    assert response.data["status"] == "success"
    assert response.data["registered"] == 1
    create_mock.assert_called_once()
    kwargs = create_mock.call_args.kwargs
    assert str(kwargs["plant_id"]) == plant_id
    assert kwargs["air_temperature"] == 28.4
    assert kwargs["soil_humidity"] == 61.2
    assert kwargs["ph_level"] == 6.4


@pytest.mark.django_db
@override_settings(HARDWARE_API_KEY="test-hw-key")
def test_sensor_data_m2m_rejects_missing_api_key():
    client = APIClient()
    payload = {
        "plant_id": str(uuid.uuid4()),
        "air_temperature": 25.0,
    }

    response = cast(Any, client.post("/api/v1/sensor-data/", data=payload, format="json"))
    assert response.status_code == 401


@pytest.mark.django_db
@override_settings(HARDWARE_API_KEY="test-hw-key")
def test_sensor_data_m2m_rejects_missing_plant_id():
    client = APIClient()
    payload = {"air_temperature": 25.0}

    response = cast(Any, client.post(
        "/api/v1/sensor-data/",
        data=payload,
        format="json",
        HTTP_X_HARDWARE_API_KEY="test-hw-key",
    ))

    assert response.status_code == 400
    assert "details" in response.data
    assert "plant_id" in response.data["details"]


@pytest.mark.django_db
@override_settings(HARDWARE_API_KEY="test-hw-key")
def test_sensor_data_m2m_accepts_null_ph_level():
    client = APIClient()
    payload = {
        "plant_id": str(uuid.uuid4()),
        "air_temperature": 24.8,
        "ph_level": None,
    }

    with patch("core.presentation.views.UserPlant.objects") as plant_qs, \
         patch("core.presentation.views.SensorLog.objects.create") as create_mock:
        plant_qs.filter.return_value.exists.return_value = True
        response = cast(Any, client.post(
            "/api/v1/sensor-data/",
            data=payload,
            format="json",
            HTTP_X_HARDWARE_API_KEY="test-hw-key",
        ))

    assert response.status_code == 201
    kwargs = create_mock.call_args.kwargs
    assert kwargs["ph_level"] is None


@pytest.mark.django_db
@override_settings(HARDWARE_API_KEY="test-hw-key")
def test_sensor_batch_m2m_bulk_insert_success():
    client = APIClient()
    pid1 = uuid.uuid4()
    pid2 = uuid.uuid4()
    payload = {
        "batch": [
            {
                "plant_id": str(pid1),
                "air_temperature": 26.1,
                "soil_humidity": 60.0,
            },
            {
                "plant_id": str(pid2),
                "air_temperature": 27.0,
                "soil_humidity": 59.4,
                "ph_level": 6.8,
            },
        ]
    }

    with patch("core.presentation.views.UserPlant.objects") as plant_qs, \
         patch("core.presentation.views.SensorLog.objects.bulk_create", return_value=[object(), object()]) as bulk_mock:
        plant_qs.filter.return_value.values_list.return_value = {pid1, pid2}
        response = cast(Any, client.post(
            "/api/v1/sensor-data/batch/",
            data=payload,
            format="json",
            HTTP_X_HARDWARE_API_KEY="test-hw-key",
        ))

    assert response.status_code == 201
    assert response.data["registered"] == 2
    bulk_mock.assert_called_once()
