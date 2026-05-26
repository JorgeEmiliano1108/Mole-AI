# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
# =============================================================================
"""
Local JWT key management for HS256 JWT verification.

Replaced Supabase JWKS (ES256) with simple local JWT secret verification.
Uses JWT_SECRET_KEY from Django settings (fallback to SECRET_KEY).
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_verification_key(token: str) -> tuple:
    """Get the correct verification key for a JWT token.
    
    Returns:
        tuple: (key, algorithms_list) suitable for jwt.decode()
    """
    # Only support HS256 with local secret
    # JWT_SECRET_KEY should be set in settings (from JWT_SECRET_KEY env var)
    secret = getattr(settings, 'JWT_SECRET_KEY', None) or settings.SECRET_KEY
    
    if not secret:
        raise ValueError("JWT_SECRET_KEY not configured — cannot verify tokens")
    
    logger.info("Using local HS256 JWT verification")
    return secret, ["HS256"]


def fetch_jwks() -> dict:
    """Public wrapper that returns empty dict (no JWKS in local mode).
    
    Kept for compatibility with existing code that may call this.
    Returns minimal JWKS-like dictionary.
    """
    logger.debug("JWKS fetch skipped — using local JWT verification")
    return {"keys": []}
