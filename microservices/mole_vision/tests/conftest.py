"""Shared fixtures for mole_vision tests."""

import pytest


@pytest.fixture
def dummy_diagnostic():
    from app.domain.entities import DiagnosticResult, SeverityLevel, ConditionCategory
    return DiagnosticResult(
        plant_id="plant-001",
        species="Tomate",
        condition="Saludable",
        condition_category=ConditionCategory.HEALTHY,
        severity=SeverityLevel.LOW,
        confidence=0.95,
        ph_predicted=6.5,
    )
