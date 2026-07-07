"""Tests for domain entities — zero mocks, pure domain."""

from datetime import datetime, timezone
from app.domain.entities import (
    DiagnosticResult, DiagnosticEvent, PlantDiagnosis,
    SeverityLevel, ConditionCategory,
    GrowthStage, AfflictionType, ProgressionStage,
)


def test_diagnostic_result_default_timestamp():
    dr = DiagnosticResult(
        plant_id="p1", species="Tomate", condition="Saludable",
        condition_category=ConditionCategory.HEALTHY,
        severity=SeverityLevel.LOW, confidence=0.95,
    )
    assert dr.plant_id == "p1"
    assert dr.timestamp is not None
    assert isinstance(dr.timestamp, datetime)


def test_diagnostic_result_is_critical():
    low = DiagnosticResult(
        plant_id="p1", species="Tomate", condition="Saludable",
        condition_category=ConditionCategory.HEALTHY,
        severity=SeverityLevel.LOW, confidence=0.95,
    )
    assert low.is_critical is False
    assert low.requires_immediate_action is False

    critical = DiagnosticResult(
        plant_id="p2", species="Tomate", condition="HLB",
        condition_category=ConditionCategory.DISEASE,
        severity=SeverityLevel.CRITICAL, confidence=0.99,
    )
    assert critical.is_critical is True
    assert critical.requires_immediate_action is True


def test_diagnostic_result_frozen():
    dr = DiagnosticResult(
        plant_id="p1", species="Tomate", condition="Saludable",
        condition_category=ConditionCategory.HEALTHY,
        severity=SeverityLevel.LOW, confidence=0.95,
    )
    import pytest
    with pytest.raises(Exception):
        dr.species = "Otra"  # frozen


def test_diagnostic_event_to_payload():
    event = DiagnosticEvent(
        event_type="diagnostic.completed",
        plant_id="abc123",
        diagnostic_id="diag-1",
        condition="Saludable",
        severity=SeverityLevel.LOW,
        ph_predicted=6.5,
        timestamp="2024-01-01T00:00:00Z",
    )
    payload = event.to_payload()
    assert payload["event_type"] == "diagnostic.completed"
    assert payload["plant_id"] == "abc123"
    assert payload["severity"] == "low"


def test_severity_level_values():
    assert SeverityLevel.LOW == "low"
    assert SeverityLevel.MEDIUM == "medium"
    assert SeverityLevel.HIGH == "high"
    assert SeverityLevel.CRITICAL == "critical"


def test_condition_category_values():
    assert ConditionCategory.HEALTHY == "healthy"
    assert ConditionCategory.DISEASE == "disease"
    assert ConditionCategory.UNKNOWN == "unknown"


# ── PlantDiagnosis ─────────────────────────────────────────────────

def test_plant_diagnosis_default_timestamp():
    pd = PlantDiagnosis(
        plant_id="p1",
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
    )
    assert pd.plant_id == "p1"
    assert pd.species_common == "Tomate"
    assert pd.growth_stage == GrowthStage.VEGETATIVA
    assert pd.affliction_name == "Tizón tardío"
    assert pd.severity == SeverityLevel.HIGH
    assert pd.progression == ProgressionStage.ADVANCED
    assert pd.confidence == 0.92
    assert pd.immediate_actions == ("Aplicar fungicida",)
    assert pd.timestamp is not None
    assert pd.model_version == "2.0.0"


def test_plant_diagnosis_healthy():
    pd = PlantDiagnosis(
        plant_id="p2",
        species_common="Maíz",
        species_scientific="Zea mays",
        growth_stage=GrowthStage.FLORACION,
        affliction_name="Ninguna",
        affliction_type=AfflictionType.PHYSIOLOGICAL,
        causal_agent="N/A",
        severity=SeverityLevel.LOW,
        progression=ProgressionStage.INITIAL,
        confidence=0.99,
        immediate_actions=(),
        preventive_measures=("Mantener monitoreo rutinario",),
        mitigation_steps=(),
    )
    assert pd.requires_immediate_action is False


def test_plant_diagnosis_critical():
    pd = PlantDiagnosis(
        plant_id="p3",
        species_common="Tomate",
        species_scientific="Solanum lycopersicum",
        growth_stage=GrowthStage.FRUCTIFICACION,
        affliction_name="Marchitez bacteriana",
        affliction_type=AfflictionType.BACTERIAL,
        causal_agent="Ralstonia solanacearum",
        severity=SeverityLevel.CRITICAL,
        progression=ProgressionStage.TERMINAL,
        confidence=0.85,
        immediate_actions=("Aislar cultivo", "Eliminar plantas infectadas"),
        preventive_measures=(),
        mitigation_steps=("Desinfección de suelo",),
    )
    assert pd.requires_immediate_action is True


def test_plant_diagnosis_confidence_clamped():
    pd = PlantDiagnosis(
        plant_id="p4",
        species_common="X",
        species_scientific="Y",
        growth_stage=GrowthStage.UNKNOWN,
        affliction_name="Ninguna",
        affliction_type=AfflictionType.UNKNOWN,
        causal_agent="Desconocido",
        severity=SeverityLevel.LOW,
        progression=ProgressionStage.INITIAL,
        confidence=2.5,
        immediate_actions=(),
        preventive_measures=(),
        mitigation_steps=(),
    )
    assert pd.confidence == 1.0


def test_plant_diagnosis_frozen():
    pd = PlantDiagnosis(
        plant_id="p5",
        species_common="X",
        species_scientific="Y",
        growth_stage=GrowthStage.UNKNOWN,
        affliction_name="Ninguna",
        affliction_type=AfflictionType.UNKNOWN,
        causal_agent="Desconocido",
        severity=SeverityLevel.LOW,
        progression=ProgressionStage.INITIAL,
        confidence=0.5,
        immediate_actions=(),
        preventive_measures=(),
        mitigation_steps=(),
    )
    import pytest
    with pytest.raises(Exception):
        pd.species_common = "Otra"


def test_growth_stage_values():
    assert GrowthStage.PLANTULA == "plántula"
    assert GrowthStage.VEGETATIVA == "vegetativa"
    assert GrowthStage.FLORACION == "floración"
    assert GrowthStage.FRUCTIFICACION == "fructificación"
    assert GrowthStage.SENESCENCIA == "senescencia"
    assert GrowthStage.UNKNOWN == "unknown"


def test_affliction_type_values():
    assert AfflictionType.PEST == "pest"
    assert AfflictionType.FUNGAL == "fungal"
    assert AfflictionType.BACTERIAL == "bacterial"
    assert AfflictionType.VIRAL == "viral"
    assert AfflictionType.NUTRIENT == "nutrient"
    assert AfflictionType.PHYSIOLOGICAL == "physiological"
    assert AfflictionType.UNKNOWN == "unknown"


def test_progression_stage_values():
    assert ProgressionStage.INITIAL == "initial"
    assert ProgressionStage.ADVANCED == "advanced"
    assert ProgressionStage.TERMINAL == "terminal"
