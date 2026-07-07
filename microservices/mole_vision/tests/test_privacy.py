"""Tests for the local privacy module (anonymize_id)."""

from app.core.privacy import anonymize_id


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
