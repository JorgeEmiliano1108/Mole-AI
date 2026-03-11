from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ai_models.services import SensorDataAggregator


def test_aggregator_returns_empty_dict_when_no_rows():
    query = Mock()
    query.filter.return_value = query
    query.order_by.return_value = query
    query.first.return_value = None

    with patch("ai_models.services.SensorLog") as sensor_log_model:
        sensor_log_model.objects.filter.return_value = query
        result = SensorDataAggregator.get_latest_sensor_readings(
            plant_id="11111111-1111-1111-1111-111111111111",
            hours_back=24,
        )

    assert result == {}


def test_aggregator_returns_flat_wide_table_fields_only():
    latest = SimpleNamespace(
        plant_id="22222222-2222-2222-2222-222222222222",
        recorded_at=datetime(2026, 3, 7, 10, 0, 0, tzinfo=timezone.utc),
        soil_humidity=63.1,
        air_temperature=27.7,
        uv_index=4.9,
        light_level=500.0,
        ph_level=None,
    )

    query = Mock()
    query.filter.return_value = query
    query.order_by.return_value = query
    query.first.return_value = latest

    with patch("ai_models.services.SensorLog") as sensor_log_model:
        sensor_log_model.objects.filter.return_value = query
        result = SensorDataAggregator.get_latest_sensor_readings(hours_back=24)

    assert result["plant_id"] == str(latest.plant_id)
    assert result["soil_humidity"] == 63.1
    assert result["air_temperature"] == 27.7
    assert result["uv_index"] == 4.9
    assert result["light_level"] == 500.0
    assert "ph_level" not in result  # nulls are intentionally omitted
