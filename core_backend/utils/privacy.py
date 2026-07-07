"""Utility functions for data privacy.

Provides a single source of truth for deterministic anonymization of identifiers
using SHA‑256. All modules that need to hash public identifiers (e.g. plant_id,
user_id, diagnostic_id) must import :func:`anonymize_id` from here.
"""

import hashlib


def anonymize_id(value: str) -> str:
    """Return a deterministic SHA‑256 hex digest of *value*.

    The function is deliberately simple – no salt – because the goal is to make
    the same identifier hash to the same value across services (so that joins
    between the Redis bus and OpenTelemetry traces are possible).
    """
    return hashlib.sha256(value.encode()).hexdigest()
