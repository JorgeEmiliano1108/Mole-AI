import json
import pytest
from unittest.mock import AsyncMock, patch

from app.infrastructure.adapters.redis_publisher import RedisEventPublisher
from app.domain.entities import DiagnosticResult

@pytest.fixture
def dummy_diagnostic():
    return DiagnosticResult(
        plant_id='plant-xyz',
        diagnostic_id='diag-xyz',
        condition='cond',
        severity='high',
        ph_predicted=None,
        timestamp=None,
    )

@pytest.mark.asyncio
async def test_otel_trace_id_propagated_to_redis_payload(dummy_diagnostic):
    # Mock the OpenTelemetry span to return a known trace_id value
    with patch('app.infrastructure.adapters.redis_publisher.ot_trace.get_current_span') as span_mock:
        span_mock.return_value.get_span_context.return_value.trace_id = 0xdeadbeefdeadbeefdeadbeefdeadbeef
        # Mock the Redis client
        with patch('app.infrastructure.adapters.redis_publisher.RedisEventPublisher._get_client') as client_get_mock:
            mock_client = AsyncMock()
            client_get_mock.return_value = mock_client
            publisher = RedisEventPublisher()
            await publisher.publish_diagnostic_completed(dummy_diagnostic, 'diag-xyz')
            # Grab the payload sent to Redis
            _, payload_json = mock_client.publish.call_args[0]
            payload = json.loads(payload_json)
            # The trace_id must be a 32‑hex string (the mocked value formatted as 32 hex)
            assert len(payload['trace_id']) == 32
            # Ensure the trace_id corresponds to the mocked value
            expected = format(0xdeadbeefdeadbeefdeadbeefdeadbeef, '032x')
            assert payload['trace_id'] == expected
