"""Tests for citation manager (I-09 coverage)."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app.infrastructure.adapters.citation_manager import CitationManager
from app.domain.schemas import SourceMetadata


@pytest.mark.asyncio
async def test_extract_sources_with_cag_data():
    mgr = CitationManager()
    sources = await mgr.extract_sources({
        "telemetria_sensores": "Sensor humedad: 45%",
        "base_conocimiento_local": "No hay documentos locales relevantes.",
        "base_conocimiento_externa": "",
    })
    assert len(sources) == 1
    assert sources[0].autor == "Sensores IoT Edge (Redis)"


@pytest.mark.asyncio
async def test_extract_sources_with_rag_data():
    mgr = CitationManager()
    sources = await mgr.extract_sources({
        "telemetria_sensores": "No hay datos de sensores en vivo.",
        "base_conocimiento_local": "Manual de cultivo de maíz",
        "base_conocimiento_externa": "",
    })
    assert len(sources) == 1
    assert "Base de Conocimiento" in sources[0].autor


@pytest.mark.asyncio
async def test_extract_sources_with_trefle():
    mgr = CitationManager()
    sources = await mgr.extract_sources({
        "telemetria_sensores": "No hay datos de sensores en vivo.",
        "base_conocimiento_local": "No hay documentos locales relevantes.",
        "base_conocimiento_externa": "Trefle.io data: Opuntia ficus-indica",
    })
    assert len(sources) == 1
    assert "Trefle.io" in sources[0].autor


@pytest.mark.asyncio
async def test_extract_sources_all_three():
    mgr = CitationManager()
    sources = await mgr.extract_sources({
        "telemetria_sensores": "Temperatura: 28C",
        "base_conocimiento_local": "Manual de riego",
        "base_conocimiento_externa": "Trefle.io data: Zea mays",
    })
    assert len(sources) == 3


@pytest.mark.asyncio
async def test_extract_sources_empty():
    mgr = CitationManager()
    sources = await mgr.extract_sources({
        "telemetria_sensores": "No hay datos de sensores en vivo.",
        "base_conocimiento_local": "No hay documentos locales relevantes.",
        "base_conocimiento_externa": "",
    })
    assert len(sources) == 0
