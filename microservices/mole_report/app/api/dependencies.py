# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
JWT ES256 JWKS validation dependency for MS3 (Reports).

Provides autonomous JWT validation using Supabase's public JWKS endpoint,
so this microservice does NOT depend on the Django monolith for auth.

Usage in FastAPI endpoints:
    from app.api.dependencies import get_current_user

    @router.post("/generate")
    def generate_report(current_user: dict = Depends(get_current_user)):
        ...
"""
import hashlib
import logging
import os
import threading
import time
from typing import Any

import jwt
import httpx
from fastapi import Header, HTTPException
from jwt.algorithms import ECAlgorithm

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
_SUPABASE_URL = os.getenv("SUPABASE_URL", os.getenv("MS3_SUPABASE_URL", ""))
_JWT_AUDIENCE = "authenticated"
_JWT_LEEWAY = 30  # seconds


# =============================================================================
# JWKS Key Cache & Validator
# =============================================================================

class JWKSValidator:
    """
    Fetches, caches and validates JWTs against Supabase JWKS (ES256).

    Thread-safe.  Keys are cached with a configurable TTL (default: 1 hour).
    Falls back to HS256 with SUPABASE_JWT_SECRET if JWKS fetch fails and
    the token header indicates HS256.
    """

    _CACHE_TTL = 3600  # 1 hour

    def __init__(self, supabase_url: str) -> None:
        self._supabase_url = supabase_url.rstrip("/") if supabase_url else ""
        self._keys: dict[str, Any] = {}
        self._last_fetched: float = 0
        self._lock = threading.Lock()

    # ── JWKS fetch ───────────────────────────────────────────────────────

    @property
    def _jwks_url(self) -> str:
        url = self._supabase_url.replace("://db.", "://")
        return f"{url}/auth/v1/.well-known/jwks.json"

    def _fetch_jwks(self) -> dict[str, Any]:
        """Fetch EC public keys from Supabase JWKS endpoint."""
        if not self._supabase_url:
            logger.warning("SUPABASE_URL not configured — JWKS fetch skipped.")
            return {}

        try:
            resp = httpx.get(self._jwks_url, timeout=10.0)
            resp.raise_for_status()
            jwks_data = resp.json()

            keys: dict[str, Any] = {}
            for key_data in jwks_data.get("keys", []):
                kid = key_data.get("kid")
                if kid and key_data.get("kty") == "EC":
                    try:
                        public_key = ECAlgorithm.from_jwk(key_data)
                        keys[kid] = public_key
                        logger.info("Loaded JWKS key: kid=%s", kid)
                    except Exception as exc:
                        logger.warning("Failed to load JWKS key %s: %s", kid, exc)
            return keys
        except Exception as exc:
            logger.error("Failed to fetch JWKS from %s: %s", self._jwks_url, exc)
            return {}

    def _ensure_keys(self, kid: str | None = None) -> None:
        """Refresh the key cache if stale or if a specific kid is missing."""
        with self._lock:
            now = time.time()
            stale = (now - self._last_fetched) > self._CACHE_TTL
            missing = kid and kid not in self._keys
            if stale or missing:
                self._keys = self._fetch_jwks()
                self._last_fetched = now

    # ── Token validation ─────────────────────────────────────────────────

    def validate_token(self, token: str) -> dict[str, Any]:
        """
        Validate a JWT and return its decoded payload.

        Raises ``jwt.InvalidTokenError`` (or subclass) on any failure.
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.DecodeError:
            raise jwt.InvalidTokenError("Cannot decode token header.")

        alg = unverified_header.get("alg", "HS256")
        kid = unverified_header.get("kid")

        # HS256 fallback (legacy Supabase projects)
        if alg == "HS256":
            secret = os.getenv("SUPABASE_JWT_SECRET", "")
            if not secret:
                raise jwt.InvalidTokenError("HS256 token but no SUPABASE_JWT_SECRET configured.")
            return jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience=_JWT_AUDIENCE,
                options={"verify_aud": True, "verify_exp": True},
                leeway=_JWT_LEEWAY,
            )

        # ES256 (modern Supabase)
        if alg == "ES256" and kid:
            self._ensure_keys(kid)
            public_key = self._keys.get(kid)
            if not public_key:
                raise jwt.InvalidTokenError(
                    f"No JWKS key for kid={kid}. Available: {list(self._keys)}"
                )
            return jwt.decode(
                token,
                public_key,
                algorithms=["ES256"],
                audience=_JWT_AUDIENCE,
                options={"verify_aud": True, "verify_exp": True},
                leeway=_JWT_LEEWAY,
            )

        raise jwt.InvalidTokenError(f"Unsupported JWT algorithm: {alg}")


# ── Singleton validator ──────────────────────────────────────────────────────
_validator = JWKSValidator(_SUPABASE_URL)


# =============================================================================
# FastAPI Dependency
# =============================================================================

def get_current_user(authorization: str = Header(..., alias="Authorization")) -> dict:
    """
    FastAPI dependency that extracts and validates a Supabase JWT from
    the ``Authorization: Bearer <token>`` header.

    Returns a dict with at least ``sub``, ``email``, ``role``, and
    ``hashed_user_id`` (SHA-256 of ``sub`` — LFPDPPP Art. 19).

    Raises:
        HTTPException(401)  on missing / invalid / expired token.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token.")

    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty Bearer token.")

    try:
        payload = _validator.validate_token(token)
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
