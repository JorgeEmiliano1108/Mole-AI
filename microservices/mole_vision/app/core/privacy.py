"""Local privacy utilities — breaks coupling with core_backend."""

import hashlib


def anonymize_id(value: str) -> str:
    """SHA-256 hash of an identifier for LFPDPPP compliance."""
    if not value:
        return "anonymous"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
