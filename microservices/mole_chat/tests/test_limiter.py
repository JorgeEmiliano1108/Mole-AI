"""Tests for app/api/limiter.py (I-09 coverage)."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app.api.limiter import limiter


def test_limiter_is_configured():
    """Rate limiter object should exist."""
    assert limiter is not None


def test_limiter_keyfunc():
    """Keyfunc should extract real client IP from X-Forwarded-For or remote_addr."""
    from starlette.requests import Request
    scope = {
        "type": "http",
        "headers": [(b"x-forwarded-for", b"203.0.113.5, 10.0.0.1")],
        "client": ("192.168.1.1", 12345),
    }
    request = Request(scope)

    from app.api.limiter import get_real_ip
    key = get_real_ip(request)
    assert key == "203.0.113.5"  # first proxy IP

    # Without X-Forwarded-For, should use client.host
    scope2 = {"type": "http", "headers": [], "client": ("10.0.0.1", 8080)}
    request2 = Request(scope2)
    key2 = get_real_ip(request2)
    assert key2 == "10.0.0.1"

    # Without client either, should use 127.0.0.1
    scope3 = {"type": "http", "headers": []}
    request3 = Request(scope3)
    key3 = get_real_ip(request3)
    assert key3 == "127.0.0.1"
