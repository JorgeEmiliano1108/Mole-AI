"""Tests for the local privacy module (anonymize_id)."""

import pytest
from app.core.privacy import anonymize_id


@pytest.fixture(autouse=True)
def _anon_key(monkeypatch):
    monkeypatch.setenv("ANONIMIZACION_KEY", "test-ms1-anon-key")


def test_anonymize_id_returns_64_char_hex():
    result = anonymize_id("user-123")
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_anonymize_id_deterministic():
    assert anonymize_id("same-value") == anonymize_id("same-value")


def test_anonymize_id_different_inputs_different():
    assert anonymize_id("a") != anonymize_id("b")


def test_anonymize_id_empty():
    assert anonymize_id("") == "anonymous"


def test_anonymize_id_none():
    assert anonymize_id(None) == "anonymous"


def test_anonymize_id_fails_closed_without_key(monkeypatch):
    monkeypatch.delenv("ANONIMIZACION_KEY", raising=False)
    with pytest.raises(RuntimeError):
        anonymize_id("user-123")


def test_anonymize_id_matches_hmac_reference():
    """Verifica que la salida sea HMAC-SHA256 real, no solo SHA-256."""
    import hashlib
    import hmac

    expected = hmac.new(
        b"test-ms1-anon-key", b"user-123", hashlib.sha256
    ).hexdigest()
    assert anonymize_id("user-123") == expected
