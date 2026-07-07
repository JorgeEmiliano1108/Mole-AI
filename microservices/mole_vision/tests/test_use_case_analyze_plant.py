"""Tests for AnalyzePlantUseCase — uses fake adapters."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.application.use_cases.analyze_plant import AnalyzePlantUseCase
from app.domain.entities import (
    PlantDiagnosis, SeverityLevel, AfflictionType,
    GrowthStage, ProgressionStage,
)


@ pytest.fixture
def fake_vision():
    client = MagicMock()
    client.is_ready.return_value = True
    client.analyze = AsyncMock(return_value=PlantDiagnosis(
        plant_id="",
        species_common="Tomate",
        species_scientific="Solanum lycopersicum",
        growth_stage=GrowthStage.VEGETATIVA,
        affliction_name="Tizón tardío",
        affliction_type=AfflictionType.FUNGAL,
        causal_agent="Phytophthora infestans",
        severity=SeverityLevel.HIGH,
        progression=ProgressionStage.ADVANCED,
        confidence=0.92,
        immediate_actions=("Aplicar fungicida",),
        preventive_measures=("Rotación de cultivos",),
        mitigation_steps=("Monitoreo semanal",),
    ))
    return client


@ pytest.fixture
def fake_events():
    pub = AsyncMock()
    pub.publish_diagnostic_completed = AsyncMock()
    pub.publish_diagnostic_failed = AsyncMock()
    return pub


@ pytest.fixture
def fake_repo():
    repo = AsyncMock()
    repo.save_diagnostic.return_value = "diag-uuid-123"
    return repo


@ pytest.fixture
def use_case(fake_vision, fake_events, fake_repo):
    return AnalyzePlantUseCase(
        vision_client=fake_vision,
        event_publisher=fake_events,
        diagnostic_repository=fake_repo,
    )


@ pytest.mark.asyncio
async def test_execute_success(use_case, fake_vision, fake_events, fake_repo):
    result = await use_case.execute(
        image_bytes=b"fake_image_bytes",
        plant_id="planta-01",
        user_claims={"sub": "user-1"},
    )
    assert result.species_common == "Tomate"
    assert result.affliction_name == "Tizón tardío"
    fake_vision.analyze.assert_awaited_once()
    fake_repo.save_diagnostic.assert_awaited_once()
    fake_events.publish_diagnostic_completed.assert_awaited_once()


@ pytest.mark.asyncio
async def test_execute_plant_id_is_hashed(use_case, fake_repo, fake_events):
    result = await use_case.execute(
        image_bytes=b"data",
        plant_id="planta-01",
    )
    assert len(result.plant_id) == 64
    assert result.plant_id.startswith("planta-01") is False


@ pytest.mark.asyncio
async def test_execute_model_not_ready(use_case, fake_vision):
    fake_vision.is_ready.return_value = False
    with pytest.raises(RuntimeError, match="Vision model not available"):
        await use_case.execute(
            image_bytes=b"data",
            plant_id="p1",
        )


@ pytest.mark.asyncio
async def test_execute_event_failure_does_not_raise(use_case, fake_events):
    fake_events.publish_diagnostic_completed.side_effect = Exception("Redis down")
    result = await use_case.execute(
        image_bytes=b"data",
        plant_id="p1",
    )
    assert result.species_common == "Tomate"
