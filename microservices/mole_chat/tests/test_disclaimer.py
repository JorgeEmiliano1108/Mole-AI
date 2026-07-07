"""Tests for Ética IA (I-08): disclaimer and generated_by field."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from pydantic import ValidationError

from app.domain.schemas import ChatResponse, COFEPRIS_DISCLAIMER


def test_chat_response_defaults():
    resp = ChatResponse(respuesta="Hola mundo")
    assert resp.respuesta == "Hola mundo"
    assert resp.disclaimer == COFEPRIS_DISCLAIMER
    assert resp.generated_by == "Mole.AI"


def test_chat_response_always_has_disclaimer():
    """Disclaimer should never be empty string."""
    resp = ChatResponse(respuesta="test", disclaimer=COFEPRIS_DISCLAIMER)
    assert resp.disclaimer
    assert len(str(resp.disclaimer)) > 10


def test_chat_response_generated_by_identifies_ai():
    resp = ChatResponse(respuesta="test")
    assert "Mole.AI" in resp.generated_by


def test_chat_response_custom_disclaimer():
    resp = ChatResponse(respuesta="test", disclaimer="Custom notice")
    assert resp.disclaimer == "Custom notice"
