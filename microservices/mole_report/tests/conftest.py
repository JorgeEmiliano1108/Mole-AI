import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def fake_env_vars(monkeypatch):
    monkeypatch.setenv("MS3_SUPABASE_URL", "http://test")
    monkeypatch.setenv("MS3_SUPABASE_KEY", "test-key")
    monkeypatch.setenv("NVIDIA_API_KEY", "test-nv-key")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-12345")
    monkeypatch.setenv("MS3_REDIS_URL", "redis://localhost:6379/2")


@pytest.fixture
def fake_job_store():
    from infrastructure.redis.job_metadata_store import JobMetadataStore

    fake_redis = MagicMock()
    fake_redis.hset.return_value = True
    fake_redis.hgetall.return_value = {"status": "QUEUED", "progress": "0"}
    return JobMetadataStore(fake_redis)


@pytest.fixture
def fake_supabase():
    from infrastructure.db.supabase_client import SupabaseClient

    client = MagicMock(spec=SupabaseClient)
    client.fetch_sensor_logs.return_value = [
        {"timestamp": "2024-01-01T00:00:00Z", "sensor": "temp_1", "value": 25.0},
        {"timestamp": "2024-01-01T01:00:00Z", "sensor": "temp_1", "value": 26.0},
    ]
    client.fetch_ai_diagnostics.return_value = []
    client.insert_audit_record.return_value = None
    return client


@pytest.fixture
def fake_nvidia():
    from infrastructure.llm.nvidia_client import NvidiaReportClient

    client = MagicMock(spec=NvidiaReportClient)
    client.synthesize_insights.return_value = {
        "summary": "Resumen de prueba",
        "text": "Análisis de prueba para auditoría.",
    }
    return client
