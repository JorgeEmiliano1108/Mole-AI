"""Tests for NvidiaReportClient — uses mock OpenAI."""

from unittest.mock import MagicMock, patch
from infrastructure.llm.nvidia_client import NvidiaReportClient


def test_synthesize_insights_no_api_key():
    client = NvidiaReportClient()
    client.client = None
    with patch("app.config.settings.nvidia_api_key", None):
        result = client.synthesize_insights(docs=[], logs=[])
    assert "Sin API Key" in result["summary"]


def test_build_user_message_with_logs():
    client = NvidiaReportClient()
    client.client = MagicMock()
    logs = [{"timestamp": "2024-01-01", "sensor": "temp_1", "value": 25.0}]
    result = client.synthesize_insights(docs=[], logs=logs)
    assert isinstance(result, dict)
    assert "summary" in result
