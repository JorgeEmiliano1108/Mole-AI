"""Tests for API-Key validation (I-06 / ETSI EN 303 645)."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch
from fastapi import HTTPException

from app.api.dependencies import verify_api_key
from app.core.config import settings


@pytest.mark.asyncio
async def test_verify_api_key_skipped_if_not_configured():
    with patch.object(settings, "API_KEY", ""):
        result = await verify_api_key(x_api_key="")
        assert result == "default-device"


@pytest.mark.asyncio
async def test_verify_api_key_valid():
    with patch.object(settings, "API_KEY", "my-secret-key"):
        result = await verify_api_key(x_api_key="my-secret-key")
        assert result == "authenticated-device"


@pytest.mark.asyncio
async def test_verify_api_key_missing():
    with patch.object(settings, "API_KEY", "my-secret-key"):
        with pytest.raises(HTTPException) as exc:
            await verify_api_key(x_api_key="")
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_api_key_invalid():
    with patch.object(settings, "API_KEY", "my-secret-key"):
        with pytest.raises(HTTPException) as exc:
            await verify_api_key(x_api_key="wrong-key")
        assert exc.value.status_code == 403
        assert "inválida" in exc.value.detail
