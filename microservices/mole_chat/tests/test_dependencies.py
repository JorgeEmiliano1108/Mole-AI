"""Tests for app/api/dependencies.py — uses FakeTokenValidator (no mocks)."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.dependencies import get_current_user, verify_api_key, security_scheme
from app.core.config import settings
from tests.fakes import FakeTokenValidator


@pytest.fixture
def valid_credentials():
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token.here")


@pytest.mark.asyncio
async def test_get_current_user_with_valid_token(valid_credentials):
    with patch("app.api.dependencies.get_token_validator") as mock_get_val:
        mock_get_val.return_value = FakeTokenValidator(return_value={"sub": "user-abc"})
        result = await get_current_user(credentials=valid_credentials)
    assert result == "user-abc"


@pytest.mark.asyncio
async def test_get_current_user_missing_sub(valid_credentials):
    with patch("app.api.dependencies.get_token_validator") as mock_get_val:
        mock_get_val.return_value = FakeTokenValidator(return_value={"aud": "test"})
        with pytest.raises(HTTPException) as exc:
            await get_current_user(credentials=valid_credentials)
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(valid_credentials):
    with patch("app.api.dependencies.get_token_validator") as mock_get_val:
        exc_to_raise = HTTPException(status_code=401, detail="Invalid token")
        mock_get_val.return_value = FakeTokenValidator(raise_exc=exc_to_raise)
        with pytest.raises(HTTPException) as exc:
            await get_current_user(credentials=valid_credentials)
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_unexpected_exception(valid_credentials):
    with patch("app.api.dependencies.get_token_validator") as mock_get_val:
        mock_get_val.return_value = FakeTokenValidator(raise_exc=RuntimeError("unexpected"))
        with pytest.raises(HTTPException) as exc:
            await get_current_user(credentials=valid_credentials)
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_api_key_configured_valid():
    with patch.object(settings, "API_KEY", "test-key"):
        result = await verify_api_key(x_api_key="test-key")
    assert result == "authenticated-device"


@pytest.mark.asyncio
async def test_verify_api_key_configured_missing():
    with patch.object(settings, "API_KEY", "test-key"):
        with pytest.raises(HTTPException) as exc:
            await verify_api_key(x_api_key="")
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_api_key_configured_wrong():
    with patch.object(settings, "API_KEY", "test-key"):
        with pytest.raises(HTTPException) as exc:
            await verify_api_key(x_api_key="wrong-key")
        assert exc.value.status_code == 403


def test_security_scheme_is_bearer():
    assert security_scheme.scheme_name == "HTTPBearer"
