"""Tests for domain schemas — Pydantic validation."""

import pytest
from datetime import datetime
from app.domain.schemas import (
    VisionInputSchema, VisionOutputSchema, DiagnosticResponseSchema,
    EventPayloadSchema, HealthCheckSchema, ConditionCategorySchema, SeverityLevelSchema,
)


def test_vision_input_valid():
    schema = VisionInputSchema(plant_id="planta-01")
    assert schema.plant_id == "planta-01"


def test_vision_input_empty_plant_id():
    with pytest.raises(Exception):
        VisionInputSchema(plant_id="")


def test_vision_output_defaults():
    schema = VisionOutputSchema(confidence=0.85)
    assert schema.species == "Desconocida"
    assert schema.condition == "No identificada"
    assert schema.confidence == 0.85
    assert schema.ph_predicted is None
    assert schema.model_version == "1.0.0"


def test_vision_output_invalid_confidence():
    with pytest.raises(Exception):
        VisionOutputSchema(confidence=1.5)


def test_diagnostic_response_schema():
    schema = DiagnosticResponseSchema(
        plant_id="p1",
        species="Tomate",
        condition="Saludable",
        condition_category=ConditionCategorySchema.HEALTHY,
        severity=SeverityLevelSchema.LOW,
        confidence=0.95,
        timestamp=datetime(2024, 1, 1),
    )
    assert schema.disclaimer.startswith("Aviso")
    assert schema.plant_id == "p1"


def test_event_payload_schema():
    schema = EventPayloadSchema(
        event_type="diagnostic.completed",
        plant_id="p1",
        diagnostic_id="diag-1",
        condition="Saludable",
        severity=SeverityLevelSchema.LOW,
        ph_predicted=6.5,
        timestamp="2024-01-01T00:00:00Z",
    )
    assert schema.event_type == "diagnostic.completed"


def test_health_check_schema():
    schema = HealthCheckSchema(status="ok")
    assert schema.status == "ok"
    assert schema.timestamp is not None
