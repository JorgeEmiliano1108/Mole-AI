"""Tests for JWT validation (ES256 via JWKS and HS256 fallback) — no MagicMock."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import jwt
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.core.security import (
    get_token_validator,
    HS256Validator,
    JWKSValidator,
    _hash_user_id,
)
from app.core.config import settings


def test_hash_user_id_returns_sha256():
    hashed = _hash_user_id("user-abc-123")
    assert isinstance(hashed, str)
    assert len(hashed) == 64
    assert hashed != "user-abc-123"


def test_hash_user_id_empty_returns_anonymous():
    assert _hash_user_id("") == "anonymous"
    assert _hash_user_id(None) == "anonymous"


@pytest.mark.asyncio
async def test_hs256_validator_valid_token():
    secret = "test-secret-key"
    with patch.object(settings, "JWT_SECRET_KEY", secret), \
         patch.object(settings, "JWT_AUDIENCE", "authenticated"), \
         patch.object(settings, "JWT_LEEWAY", 30), \
         patch.object(settings, "JWKS_URL", ""):
        validator = HS256Validator()
        token = jwt.encode(
            {
                "sub": "user-123",
                "aud": "authenticated",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            secret,
            algorithm="HS256",
        )
        claims = await validator.validate(token)
        assert claims["sub"] == "user-123"


@pytest.mark.asyncio
async def test_hs256_validator_expired_token():
    secret = "test-secret-key"
    with patch.object(settings, "JWT_SECRET_KEY", secret), \
         patch.object(settings, "JWT_AUDIENCE", "authenticated"), \
         patch.object(settings, "JWT_LEEWAY", 0):
        validator = HS256Validator()
        token = jwt.encode(
            {
                "sub": "user-123",
                "aud": "authenticated",
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            },
            secret,
            algorithm="HS256",
        )
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await validator.validate(token)
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_hs256_validator_bad_audience():
    secret = "test-secret-key"
    with patch.object(settings, "JWT_SECRET_KEY", secret), \
         patch.object(settings, "JWT_AUDIENCE", "authenticated"), \
         patch.object(settings, "JWT_LEEWAY", 0):
        validator = HS256Validator()
        token = jwt.encode(
            {
                "sub": "user-123",
                "aud": "other-app",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            secret,
            algorithm="HS256",
        )
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await validator.validate(token)
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_jwks_validator_valid_token():
    """Test JWKS validator with a real ES256 key pair — cache populated directly."""
    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    kid = "test-key-1"
    token = jwt.encode(
        {
            "sub": "user-123",
            "aud": "authenticated",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        private_key,
        algorithm="ES256",
        headers={"kid": kid},
    )

    with patch.object(settings, "JWKS_URL", "https://example.com/.well-known/jwks"), \
         patch.object(settings, "JWT_AUDIENCE", "authenticated"), \
         patch.object(settings, "JWT_LEEWAY", 30), \
         patch.object(settings, "JWT_ALGORITHM", "ES256"):
        validator = JWKSValidator()
        # Pre-populate cache to avoid network fetch
        validator._client._cached_keys = {kid: public_key}
        validator._client._cache_timestamp = time.time() + 3600  # far in future

        claims = await validator.validate(token)
        assert claims["sub"] == "user-123"


@pytest.mark.asyncio
async def test_jwks_validator_unknown_kid():
    from cryptography.hazmat.primitives.asymmetric import ec
    private_key = ec.generate_private_key(ec.SECP256R1())

    token = jwt.encode(
        {"sub": "user-123", "aud": "authenticated",
         "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        private_key,
        algorithm="ES256",
        headers={"kid": "unknown-key"},
    )

    with patch.object(settings, "JWKS_URL", "https://example.com/.well-known/jwks"), \
         patch.object(settings, "JWT_AUDIENCE", "authenticated"), \
         patch.object(settings, "JWT_LEEWAY", 30), \
         patch.object(settings, "JWT_ALGORITHM", "ES256"):
        validator = JWKSValidator()
        validator._client._cached_keys = {"other-key": "dummy"}
        validator._client._cache_timestamp = time.time() + 3600

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await validator.validate(token)
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_token_validator_returns_hs256_when_no_jwks():
    with patch.object(settings, "JWKS_URL", ""):
        validator = get_token_validator()
        assert isinstance(validator, HS256Validator)


@pytest.mark.asyncio
async def test_get_token_validator_returns_jwks_when_jwks_set():
    with patch.object(settings, "JWKS_URL", "https://example.com/jwks"):
        import app.core.security as sec_module
        sec_module._token_validator = None
        validator = get_token_validator()
        assert isinstance(validator, JWKSValidator)
