"""Tests for NOM-059-SEMARNAT species protection."""

import pytest
from app.core.nom059 import check_nom059_violation, NOM059_SENTINEL
from app.domain.entities import (
    PlantDiagnosis, SeverityLevel, AfflictionType,
    GrowthStage, ProgressionStage,
)


def _make_diagnosis(
    species_common: str = "Tomate",
    species_scientific: str = "Solanum lycopersicum",
    affliction_name: str = "Tizón tardío",
) -> PlantDiagnosis:
    return PlantDiagnosis(
        plant_id="p1",
        species_common=species_common,
        species_scientific=species_scientific,
        growth_stage=GrowthStage.VEGETATIVA,
        affliction_name=affliction_name,
        affliction_type=AfflictionType.FUNGAL,
        causal_agent="Phytophthora infestans",
        severity=SeverityLevel.HIGH,
        progression=ProgressionStage.ADVANCED,
        confidence=0.92,
        immediate_actions=("Aplicar fungicida",),
        preventive_measures=("Rotación de cultivos",),
        mitigation_steps=("Monitoreo semanal",),
    )


def test_healthy_crop_not_blocked():
    d = _make_diagnosis()
    assert check_nom059_violation(d) is False


def test_llm_sentinel_blocks():
    d = _make_diagnosis(affliction_name=NOM059_SENTINEL)
    assert check_nom059_violation(d) is True


def test_biznaga_in_species_blocked():
    d = _make_diagnosis(
        species_common="Biznaga barril",
        species_scientific="Echinocactus platyacanthus",
    )
    assert check_nom059_violation(d) is True


def test_cactacea_in_species_blocked():
    d = _make_diagnosis(
        species_common="Cactácea desconocida",
        species_scientific="Cactaceae sp.",
    )
    assert check_nom059_violation(d) is True


def test_nom059_reference_blocked():
    d = _make_diagnosis(
        species_common="Planta bajo NOM-059",
        species_scientific="Especie protegida",
    )
    assert check_nom059_violation(d) is True


def test_cientifico_con_protegida_blocked():
    d = _make_diagnosis(
        species_common="Maguey",
        species_scientific="Sujeta a protección especial",
    )
    assert check_nom059_violation(d) is True


def test_maderas_preciosas_blocked():
    d = _make_diagnosis(
        species_common="Caoba",
        species_scientific="Swietenia macrophylla",
        affliction_name="Tala ilegal de maderas preciosas",
    )
    assert check_nom059_violation(d) is True


def test_case_insensitive():
    d = _make_diagnosis(
        species_common="BIZNAGA",
        species_scientific="ECHINOCACTUS",
    )
    assert check_nom059_violation(d) is True
