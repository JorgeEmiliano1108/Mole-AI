import asyncio
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from application.use_cases.explain_ph_use_case import ExplainPhUseCase
from domain.services.validator_service import SensorValidator


class DummyKnowledgeRepo:
    async def get_ph_tolerance(self, species_name):
        return None

    async def save_ph_tolerance(self, species_name, tolerance):
        return None


class DummyBotanicalGateway:
    async def fetch_tolerance(self, species_name):
        return None


def test_explain_use_case_accepts_wide_table_air_temperature_and_null_ph_level():
    """Thermal/humidity alerts use the fallback branch (sensor_validator=None)
    which checks air_temperature > 35 and humidity < 20 thresholds."""
    use_case = ExplainPhUseCase(
        knowledge_repo=DummyKnowledgeRepo(),
        botanical_gateway=DummyBotanicalGateway(),
        sensor_validator=None,
    )

    result = asyncio.run(
        use_case.execute(
            ph_cnn=6.7,
            plant_id="33333333-3333-3333-3333-333333333333",
            sensors={
                "air_temperature": 36.2,
                "soil_humidity": 19.0,
                "uv_index": 7.1,
                "ph_level": None,
            },
            species_name=None,
        )
    )

    assert result.ph_status in {"optimal", "warning", "critical"}
    assert "alerts" in result.sensor_context
    # Wide-table thermal alert must not be lost due to naming mismatch
    assert any("ESTRÉS TÉRMICO" in a for a in result.sensor_context["alerts"])
    # ph_level=None must propagate without crash
    assert result.sensor_context.get("ph_level") is None


def test_explain_use_case_sensor_validator_accepts_normal_readings():
    """When SensorValidator is injected, normal readings produce zero alerts."""
    use_case = ExplainPhUseCase(
        knowledge_repo=DummyKnowledgeRepo(),
        botanical_gateway=DummyBotanicalGateway(),
        sensor_validator=SensorValidator(),
    )

    result = asyncio.run(
        use_case.execute(
            ph_cnn=6.5,
            plant_id="33333333-3333-3333-3333-333333333333",
            sensors={
                "air_temperature": 25.0,
                "soil_humidity": 55.0,
                "uv_index": 5.0,
                "ph_level": 6.3,
            },
            species_name=None,
        )
    )

    assert result.ph_status == "optimal"
    assert result.sensor_context["alerts"] == []


def test_explain_use_case_handles_empty_sensor_dict_without_crash():
    use_case = ExplainPhUseCase(
        knowledge_repo=DummyKnowledgeRepo(),
        botanical_gateway=DummyBotanicalGateway(),
        sensor_validator=SensorValidator(),
    )

    result = asyncio.run(
        use_case.execute(
            ph_cnn=6.2,
            plant_id="44444444-4444-4444-4444-444444444444",
            sensors={},
            species_name=None,
        )
    )

    assert result.confidence == "low"
    assert result.data_sources == ["hardcoded_default"]
    assert result.sensor_context.get("alerts") == []
