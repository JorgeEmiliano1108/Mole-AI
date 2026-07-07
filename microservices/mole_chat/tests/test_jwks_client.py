"""Tests for JWKSClient — no mocks, manual cache population and _fetch_keys replacement."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import time

from app.core.jwks_client import JWKSClient


def _make_jwk_dict():
    """Create a minimal valid EC JWK dict with a real key pair."""
    from cryptography.hazmat.primitives.asymmetric import ec
    import base64
    private_key = ec.generate_private_key(ec.SECP256R1())
    pub = private_key.public_key().public_numbers()

    def b64u(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

    return {
        "keys": [{
            "kty": "EC",
            "kid": "key-1",
            "x": b64u(pub.x.to_bytes(32, 'big')),
            "y": b64u(pub.y.to_bytes(32, 'big')),
            "crv": "P-256",
            "alg": "ES256",
        }]
    }


def _populate_cache(client, jwks):
    """Populate the client's cache with a real EC public key from a JWK dict."""
    from cryptography.hazmat.primitives.asymmetric import ec
    from app.core.jwks_client import _base64url_decode
    jwk = jwks["keys"][0]
    x_bytes = _base64url_decode(jwk["x"])
    y_bytes = _base64url_decode(jwk["y"])
    public_key = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256R1(), b'\x04' + x_bytes + y_bytes
    )
    client._cached_keys = {jwk["kid"]: public_key}
    client._cache_timestamp = time.time()


@pytest.mark.asyncio
async def test_get_public_key_cache_hit():
    jwks = _make_jwk_dict()
    client = JWKSClient("https://example.com/jwks", cache_ttl=300)
    _populate_cache(client, jwks)

    key = await client.get_public_key("key-1")
    assert key is not None


@pytest.mark.asyncio
async def test_get_public_key_unknown_kid():
    client = JWKSClient("https://example.com/jwks", cache_ttl=300)
    client._cached_keys = {"other-key": "dummy"}
    client._cache_timestamp = time.time()

    key = await client.get_public_key("unknown-kid")
    assert key is None


@pytest.mark.asyncio
async def test_fetch_keys_success():
    """Patched _fetch_keys to return a cached key."""
    jwks = _make_jwk_dict()
    client = JWKSClient("https://example.com/jwks", cache_ttl=300)

    async def mock_fetch():
        from cryptography.hazmat.primitives.asymmetric import ec
        from app.core.jwks_client import _base64url_decode
        jwk = jwks["keys"][0]
        x_bytes = _base64url_decode(jwk["x"])
        y_bytes = _base64url_decode(jwk["y"])
        client._cached_keys = {
            jwk["kid"]: ec.EllipticCurvePublicKey.from_encoded_point(
                ec.SECP256R1(), b'\x04' + x_bytes + y_bytes
            )
        }
        client._cache_timestamp = time.time()

    client._fetch_keys = mock_fetch
    client._cache_timestamp = 0  # force expiry
    key = await client.get_public_key("key-1")
    assert key is not None


@pytest.mark.asyncio
async def test_fetch_keys_no_jwks_url():
    client = JWKSClient("", cache_ttl=300)
    client._cache_timestamp = 0
    key = await client.get_public_key("any")
    assert key is None


@pytest.mark.asyncio
async def test_close_session_no_session():
    client = JWKSClient("https://example.com/jwks", cache_ttl=300)
    await client.close()
    assert client._session is None or client._session.closed


@pytest.mark.asyncio
async def test_close_existing_session():
    """close() should close the session if it exists."""
    import aiohttp
    client = JWKSClient("https://example.com/jwks", cache_ttl=300)
    client._session = aiohttp.ClientSession()
    assert not client._session.closed
    await client.close()
    assert client._session.closed


@pytest.mark.asyncio
async def test_get_public_key_no_keys_in_cache():
    client = JWKSClient("https://example.com/jwks", cache_ttl=300)
    client._cache_timestamp = time.time()  # cache is fresh
    key = await client.get_public_key("any")
    assert key is None
