"""
JWKS Client - Fetches and caches public keys for ES256 JWT verification.
Zero-Trust: offline validation possible after cache is warm.
"""
import asyncio
import time
from typing import Optional

import aiohttp
import structlog
from jwt.algorithms import RSAAlgorithm
from cryptography.hazmat.primitives.asymmetric import ec

logger = structlog.get_logger()


class JWKSClient:
    """Fetches JWKS from a configurable URL and caches keys with TTL.
    Thread-safe (async lock) for concurrent requests.
    """

    def __init__(self, jwks_url: str, cache_ttl: int = 300):
        self._jwks_url = jwks_url
        self._cache_ttl = cache_ttl
        self._cached_keys: dict[str, ec.EllipticCurvePublicKey] | None = None
        self._cache_timestamp: float = 0.0
        self._lock = asyncio.Lock()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def get_public_key(self, kid: str) -> Optional[ec.EllipticCurvePublicKey]:
        """Get a public key by its Key ID (kid), refreshing cache if needed."""
        if self._is_cache_expired():
            async with self._lock:
                if self._is_cache_expired():
                    await self._fetch_keys()
        if self._cached_keys:
            return self._cached_keys.get(kid)
        return None

    def _is_cache_expired(self) -> bool:
        return (time.time() - self._cache_timestamp) > self._cache_ttl

    async def _fetch_keys(self):
        """Fetch JWKS from endpoint and parse public keys."""
        if not self._jwks_url:
            logger.warning("jwks_url_not_configured")
            return
        try:
            session = await self._get_session()
            async with session.get(self._jwks_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    logger.error("jwks_fetch_failed", status=resp.status)
                    return
                jwks = await resp.json()
        except Exception as e:
            logger.error("jwks_fetch_error", error=str(e))
            return

        keys = jwks.get("keys", [])
        parsed: dict[str, ec.EllipticCurvePublicKey] = {}
        for jwk in keys:
            kid = jwk.get("kid")
            if not kid:
                continue
            try:
                if jwk.get("kty") == "EC":
                    x_bytes = _base64url_decode(jwk["x"])
                    y_bytes = _base64url_decode(jwk["y"])
                    public_key = ec.EllipticCurvePublicKey.from_encoded_point(
                        ec.SECP256R1(), b'\x04' + x_bytes + y_bytes
                    )
                    parsed[kid] = public_key
                elif jwk.get("kty") == "RSA":
                    public_key = RSAAlgorithm.from_jwk(jwk)
                    parsed[kid] = public_key  # type: ignore
            except Exception as e:
                logger.warning("jwks_key_parse_failed", kid=kid, error=str(e))

        self._cached_keys = parsed
        self._cache_timestamp = time.time()
        logger.info("jwks_cache_updated", key_count=len(parsed))

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


# Helper: same padding as PyJWT
import base64


def _base64url_decode(input_str: str) -> bytes:
    rem = len(input_str) % 4
    if rem:
        input_str += "=" * (4 - rem)
    return base64.urlsafe_b64decode(input_str)
