"""Tests for SupabaseClient — uses mock transport."""

from unittest.mock import MagicMock, patch
from infrastructure.db.supabase_client import SupabaseClient


def test_fetch_sensor_logs_empty_url():
    client = SupabaseClient(url=None, key="test")
    assert client.fetch_sensor_logs() == []


def test_fetch_ai_diagnostics_empty_url():
    client = SupabaseClient(url=None, key="test")
    assert client.fetch_ai_diagnostics() == []


def test_insert_audit_record_empty_url():
    client = SupabaseClient(url=None, key="test")
    assert client.insert_audit_record("test", {"a": 1}) is None


def test_from_env():
    with patch("app.config.settings.ms3_supabase_url", "http://test"):
        with patch("app.config.settings.ms3_supabase_key", "key"):
            client = SupabaseClient.from_env()
            assert client.url == "http://test"
            assert client.key == "key"
