"""Tests for NvidiaVisionAdapter — focuses on JSON parsing logic."""

import pytest
from app.infrastructure.adapters.nvidia_vision_adapter import NvidiaVisionAdapter
from app.domain.entities import (
    PlantDiagnosis, SeverityLevel, AfflictionType,
    GrowthStage, ProgressionStage,
)


def test_parse_response_valid_json():
    adapter = NvidiaVisionAdapter()
    raw = '''{
        "species_common": "Tomate",
        "species_scientific": "Solanum lycopersicum",
        "growth_stage": "VEGETATIVA",
        "affliction_name": "Tizón tardío",
        "affliction_type": "FUNGAL",
        "causal_agent": "Phytophthora infestans",
        "severity": "HIGH",
        "progression": "ADVANCED",
        "confidence": 0.92,
        "immediate_actions": ["Aplicar fungicida"],
        "preventive_measures": ["Rotación de cultivos"],
        "mitigation_steps": ["Monitoreo semanal"],
        "ph_predicted": 6.5
    }'''
    result = adapter._parse_response(raw)
    assert isinstance(result, PlantDiagnosis)
    assert result.species_common == "Tomate"
    assert result.species_scientific == "Solanum lycopersicum"
    assert result.growth_stage == GrowthStage.VEGETATIVA
    assert result.affliction_name == "Tizón tardío"
    assert result.affliction_type == AfflictionType.FUNGAL
    assert result.causal_agent == "Phytophthora infestans"
    assert result.severity == SeverityLevel.HIGH
    assert result.progression == ProgressionStage.ADVANCED
    assert result.confidence == 0.92
    assert result.immediate_actions == ("Aplicar fungicida",)
    assert result.ph_predicted == 6.5


def test_parse_response_with_markdown_fence():
    adapter = NvidiaVisionAdapter()
    raw = '```json\n{"species_common": "Maíz", "species_scientific": "Zea mays", "growth_stage": "FLORACION", "affliction_name": "Roya", "affliction_type": "FUNGAL", "causal_agent": "Puccinia sorghi", "severity": "HIGH", "progression": "ADVANCED", "confidence": 0.88, "immediate_actions": [], "preventive_measures": [], "mitigation_steps": []}\n```'
    result = adapter._parse_response(raw)
    assert result.species_common == "Maíz"
    assert result.ph_predicted is None


def test_parse_response_malformed_json():
    adapter = NvidiaVisionAdapter()
    raw = "Not JSON at all"
    result = adapter._parse_response(raw)
    assert result.species_common == "Desconocida"
    assert result.confidence == 0.0


def test_parse_response_confidence_clamped():
    adapter = NvidiaVisionAdapter()
    raw = '{"species_common": "X", "species_scientific": "Y", "growth_stage": "UNKNOWN", "affliction_name": "Ninguna", "affliction_type": "PEST", "causal_agent": "Desconocido", "severity": "MEDIUM", "progression": "INITIAL", "confidence": 2.5, "immediate_actions": [], "preventive_measures": [], "mitigation_steps": []}'
    result = adapter._parse_response(raw)
    assert result.confidence == 1.0


def test_parse_response_unknown_severity_fallback():
    adapter = NvidiaVisionAdapter()
    raw = '{"species_common": "X", "species_scientific": "Y", "growth_stage": "UNKNOWN", "affliction_name": "Ninguna", "affliction_type": "PEST", "causal_agent": "Desconocido", "severity": "EXTREME", "progression": "INITIAL", "confidence": 0.5, "immediate_actions": [], "preventive_measures": [], "mitigation_steps": []}'
    result = adapter._parse_response(raw)
    assert result.severity == SeverityLevel.MEDIUM


def test_parse_response_unknown_affliction_type_fallback():
    adapter = NvidiaVisionAdapter()
    raw = '{"species_common": "X", "species_scientific": "Y", "growth_stage": "UNKNOWN", "affliction_name": "Ninguna", "affliction_type": "BOGUS", "causal_agent": "Desconocido", "severity": "LOW", "progression": "INITIAL", "confidence": 0.5, "immediate_actions": [], "preventive_measures": [], "mitigation_steps": []}'
    result = adapter._parse_response(raw)
    assert result.affliction_type == AfflictionType.UNKNOWN


def test_parse_response_ph_out_of_range():
    adapter = NvidiaVisionAdapter()
    raw = '{"species_common": "X", "species_scientific": "Y", "growth_stage": "UNKNOWN", "affliction_name": "Ninguna", "affliction_type": "PEST", "causal_agent": "Desconocido", "severity": "LOW", "progression": "INITIAL", "confidence": 0.9, "ph_predicted": 99, "immediate_actions": [], "preventive_measures": [], "mitigation_steps": []}'
    result = adapter._parse_response(raw)
    assert result.ph_predicted == 14.0


def test_parse_response_non_list_actions():
    adapter = NvidiaVisionAdapter()
    raw = '{"species_common": "X", "species_scientific": "Y", "growth_stage": "UNKNOWN", "affliction_name": "Ninguna", "affliction_type": "PEST", "causal_agent": "Desconocido", "severity": "LOW", "progression": "INITIAL", "confidence": 0.9, "immediate_actions": null, "preventive_measures": "not_a_list", "mitigation_steps": [], "ph_predicted": null}'
    result = adapter._parse_response(raw)
    assert result.immediate_actions == ()
    assert result.preventive_measures == ()
