"""
Supabase JWKS key management for ES256 JWT verification.

Fetches and caches the Supabase public signing keys from the JWKS endpoint.
This is required because Supabase now uses ES256 (ECDSA) instead of HS256 (HMAC),
and ES256 verification requires the public key, not the JWT secret.
"""
import logging
import time
import threading
from typing import Optional

import jwt
import requests
from jwt.algorithms import ECAlgorithm

logger = logging.getLogger(__name__)

# Cache for JWKS keys
_jwks_cache = {
    "keys": {},
    "last_fetched": 0,
    "ttl": 3600,  # Refresh keys every hour
}
_cache_lock = threading.Lock()


def _get_jwks_url(supabase_url: str) -> str:
    """Derive JWKS URL from Supabase URL.
    
    Supabase URL in .env might be:
      - https://db.xxx.supabase.co  (database host)
      - https://xxx.supabase.co     (API host)
    
    The JWKS endpoint is always at:
      https://xxx.supabase.co/auth/v1/.well-known/jwks.json
    """
    url = supabase_url.rstrip("/")
    # Remove db. prefix if present
    url = url.replace("://db.", "://")
    return f"{url}/auth/v1/.well-known/jwks.json"


def _fetch_jwks(supabase_url: str) -> dict:
    """Fetch JWKS from Supabase."""
    jwks_url = _get_jwks_url(supabase_url)
    logger.info(f"Fetching JWKS from: {jwks_url}")
    
    try:
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        jwks_data = response.json()
        
        keys = {}
        for key_data in jwks_data.get("keys", []):
            kid = key_data.get("kid")
            if kid and key_data.get("kty") == "EC":
                try:
                    public_key = ECAlgorithm.from_jwk(key_data)
                    keys[kid] = public_key
                    logger.info(f"Loaded JWKS key: kid={kid}")
                except Exception as e:
                    logger.warning(f"Failed to load JWKS key {kid}: {e}")
        
        return keys
    except Exception as e:
        logger.error(f"Failed to fetch JWKS from {jwks_url}: {e}")
        return {}


def get_verification_key(supabase_url: str, token: str) -> tuple:
    """Get the correct verification key and algorithm for a JWT token.
    
    Returns:
        tuple: (key, algorithms_list) suitable for jwt.decode()
    """
    global _jwks_cache
    
    # Decode header without verification to get algorithm and kid
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.exceptions.DecodeError:
        raise jwt.InvalidTokenError("Cannot decode token header")
    
    alg = unverified_header.get("alg", "HS256")
    kid = unverified_header.get("kid")
    
    # HS256: Use the symmetric JWT secret directly
    if alg == "HS256":
        from django.conf import settings
        return settings.SUPABASE_JWT_SECRET, ["HS256"]
    
    # ES256: Need to fetch the public key from JWKS
    if alg == "ES256" and kid:
        with _cache_lock:
            now = time.time()
            # Refresh cache if expired or key not found
            if (now - _jwks_cache["last_fetched"] > _jwks_cache["ttl"]) or \
               (kid not in _jwks_cache["keys"]):
                _jwks_cache["keys"] = _fetch_jwks(supabase_url)
                _jwks_cache["last_fetched"] = now
            
            public_key = _jwks_cache["keys"].get(kid)
        
        if public_key:
            return public_key, ["ES256"]
        else:
            raise jwt.InvalidTokenError(
                f"No matching JWKS key for kid={kid}. "
                f"Available keys: {list(_jwks_cache['keys'].keys())}"
            )
    
    raise jwt.InvalidTokenError(f"Unsupported algorithm: {alg}")
