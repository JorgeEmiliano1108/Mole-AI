from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.routing import APIRouter
from fastapi.testclient import TestClient

from infrastructure.api.routes import create_routes


class DummyEmbeddingUseCase:
    async def execute(self, _):
        return SimpleNamespace(vector=[0.1], dimension=1, model_used="dummy", processing_time_ms=1.0)


class DummyChatUseCase:
    async def execute(self, _):
        return SimpleNamespace(answer="ok", model_used="dummy", tokens_generated=1, processing_time_ms=1.0)


class DummyHealthUseCase:
    async def execute(self):
        return SimpleNamespace(is_healthy=True, uptime_seconds=1.0, version="test", models_status=[])


class DummyIngestUseCase:
    async def execute(self, *_):
        return {"chunks_added": 1}


class DummyExplainUseCase:
    def __init__(self):
        self.last_plant_id = None

    async def execute(self, ph_cnn, plant_id, sensors, species_name=None):
        self.last_plant_id = plant_id
        return SimpleNamespace(
            ph_raw=ph_cnn,
            ph_status="warning",
            deviation=0.2,
            reasoning="ok",
            recommendations=[],
            sensor_context={**(sensors or {}), "alerts": []},
            species_used=species_name or "default",
            confidence="low",
            data_sources=["hardcoded_default"],
        )


def _build_client(explain_uc):
    # Patch the module-level router so each call starts clean
    import infrastructure.api.routes as routes_mod
    fresh_router = APIRouter(tags=["AI Services"])
    original_router = routes_mod.api_v1_router
    routes_mod.api_v1_router = fresh_router
    try:
        app = FastAPI()
        router = create_routes(
            embedding_use_case=cast(Any, DummyEmbeddingUseCase()),
            chat_use_case=cast(Any, DummyChatUseCase()),
            mole_ai_chat_use_case=cast(Any, DummyChatUseCase()),
            health_use_case=cast(Any, DummyHealthUseCase()),
            ingest_knowledge_use_case=cast(Any, DummyIngestUseCase()),
            explain_ph_use_case=cast(Any, explain_uc),
        )
        app.include_router(router, prefix="/api/v1")
        return TestClient(app)
    finally:
        routes_mod.api_v1_router = original_router


def test_explain_ph_rejects_invalid_uuid_in_plant_id():
    client = _build_client(DummyExplainUseCase())

    response = client.post(
        "/api/v1/explain/ph",
        json={
            "ph_cnn": 6.5,
            "plant_id": "not-a-uuid",
            "sensors": {"air_temperature": 25.0, "soil_humidity": 60.0},
        },
    )

    assert response.status_code == 422


def test_explain_ph_accepts_uuid_and_passes_string_to_use_case():
    explain_uc = DummyExplainUseCase()
    client = _build_client(explain_uc)
    valid_uuid = "55555555-5555-5555-5555-555555555555"

    response = client.post(
        "/api/v1/explain/ph",
        json={
            "ph_cnn": 6.3,
            "plant_id": valid_uuid,
            "sensors": {"air_temperature": 24.9, "soil_humidity": 58.1, "ph_level": None},
        },
    )

    assert response.status_code == 200
    assert response.json()["sensor_context"]["ph_level"] is None
    assert explain_uc.last_plant_id == valid_uuid
