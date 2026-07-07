# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Local JWT validation dependency for MS3 (Reports).

Provides autonomous JWT validation using local JWT_SECRET_KEY (HS256).
No dependency on Supabase or external JWKS endpoints.
"""

import hashlib
import logging

import jwt
from fastapi import Header, HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────
_JWT_SECRET = settings.jwt_secret_key
_JWT_AUDIENCE = "authenticated"
_JWT_LEEWAY = 30  # seconds


# =============================================================================
# FastAPI Dependency
# =============================================================================

def get_current_user(authorization: str = Header(..., alias="Authorization")) -> dict:
    """
    FastAPI dependency that extracts and validates a local JWT from
    the ``Authorization: Bearer <token>`` header.

    Returns a dict with at least ``sub``, ``email``, ``role``, and
    ``hashed_user_id`` (SHA-256 of ``sub`` — LFPDPPP Art. 19).

    Raises:
        HTTPException(401) on missing / invalid / expired token.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token.")

    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty Bearer token.")

    if not _JWT_SECRET:
        logger.error("JWT_SECRET_KEY not configured — cannot validate tokens")
        raise HTTPException(status_code=500, detail="Server auth configuration error.")

    try:
        payload = jwt.decode(
            token,
            _JWT_SECRET,
            algorithms=["HS256"],
            audience=_JWT_AUDIENCE,
            options={"verify_aud": True, "verify_exp": True},
            leeway=_JWT_LEEWAY,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")

    sub = payload.get("sub")
    email = payload.get("email")

    if not sub or not email:
        raise HTTPException(
            status_code=401,
            detail="Token payload missing required claims (sub, email).",
        )

    hashed_uid = hashlib.sha256(str(sub).encode("utf-8")).hexdigest()

    return {
        "sub": sub,
        "email": email,
        "role": payload.get("role", "authenticated"),
        "hashed_user_id": hashed_uid,
    }
