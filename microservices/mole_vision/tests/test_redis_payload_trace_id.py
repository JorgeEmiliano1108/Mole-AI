import json
import pytest
from unittest.mock import AsyncMock, patch

from app.infrastructure.adapters.redis_publisher import RedisEventPublisher
from app.domain.entities import DiagnosticResult, SeverityLevel, ConditionCategory


@pytest.fixture
def dummy_diagnostic():
    return DiagnosticResult(
        plant_id="plant-123",
        species="Tomate",
        condition="some-condition",
        condition_category=ConditionCategory.UNKNOWN,
        severity=SeverityLevel.MEDIUM,
        confidence=0.85,
        ph_predicted=None,
    )


@pytest.mark.asyncio
async def test_redis_payload_contains_trace_id_and_hashes(dummy_diagnostic):
    with patch("app.infrastructure.adapters.redis_publisher.ot_trace.get_current_span") as span_mock:
        span_mock.return_value.get_span_context.return_value.trace_id = 0
        with patch("app.infrastructure.adapters.redis_publisher.RedisEventPublisher._get_client") as get_client_mock:
            mock_client = AsyncMock()
            get_client_mock.return_value = mock_client
            publisher = RedisEventPublisher()
            await publisher.publish_diagnostic_completed(dummy_diagnostic, "diag-456")
            assert mock_client.publish.await_count == 1
            _, payload_json = mock_client.publish.call_args[0]
            payload = json.loads(payload_json)
            assert payload["trace_id"] == "0" * 32
            assert len(payload.get("plant_id", "")) == 64
            assert len(payload.get("diagnostic_id", "")) == 64
