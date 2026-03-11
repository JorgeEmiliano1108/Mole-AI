"""
BotanicalFallbackGateway — External Plant Data Adapters
==========================================================
Implements the "Race with Fallback" pattern:
  • Both adapters are called in parallel via asyncio.gather
  • The first valid response wins (Trefle preferred)
  • If both fail, returns None → caller uses hardcoded default
  • Results are persisted to Supabase by the Use Case (idempotent)

Free tier limits:
  - Trefle.io : ~100 requests/hour
  - FarmVillage: TBD (check their docs)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

TREFLE_BASE = "https://trefle.io/api/v1"
FARMVILLAGE_BASE = "https://api.farmvillage.io/v1"  # Update when confirmed


# ──────────────────────────────────────────────────────────────────────────────
# Adapters
# ──────────────────────────────────────────────────────────────────────────────

class TrefleAdapter:
    """
    Adapter for Trefle.io global plant database.
    Free tier: ~100 req/hour — protected by Supabase Capa Cero caching.
    """

    def __init__(self, api_token: str, http_client: httpx.AsyncClient):
        self._token = api_token
        self._client = http_client

    async def fetch_ph_tolerance(self, species_name: str) -> Optional[dict]:
        if not self._token:
            logger.debug("Trefle token not configured, skipping.")
            return None
        try:
            resp = await self._client.get(
                f"{TREFLE_BASE}/plants/search",
                params={"q": species_name, "token": self._token},
                timeout=5.0,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if not data:
                return None
            plant = data[0].get("main_species", data[0])
            growth = plant.get("growth", {})
            ph_min = growth.get("ph_minimum")
            ph_max = growth.get("ph_maximum")
            if ph_min is None or ph_max is None:
                return None
            return {
                "min": float(ph_min),
                "max": float(ph_max),
                "optimal": round((float(ph_min) + float(ph_max)) / 2, 1),
                "source": "trefle",
                "scientific_name": plant.get("scientific_name"),
            }
        except httpx.HTTPStatusError as e:
            logger.warning("Trefle HTTP %s for '%s'", e.response.status_code, species_name)
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as e:
            logger.warning("Trefle error for '%s': %s", species_name, e)
        return None


class FarmVillageAdapter:
    """
    Adapter for FarmVillage — focused on Mesoamerican crops.
    Acts as secondary fallback if Trefle returns no data.
    """

    def __init__(self, api_key: str, http_client: httpx.AsyncClient):
        self._key = api_key
        self._client = http_client

    async def fetch_ph_tolerance(self, species_name: str) -> Optional[dict]:
        if not self._key:
            logger.debug("FarmVillage key not configured, skipping.")
            return None
        try:
            resp = await self._client.get(
                f"{FARMVILLAGE_BASE}/crops/ph",
                params={"species": species_name},
                headers={"X-Api-Key": self._key},
                timeout=5.0,
            )
            resp.raise_for_status()
            data = resp.json()
            ph_min = float(data["ph_min"])
            ph_max = float(data["ph_max"])
            return {
                "min": ph_min,
                "max": ph_max,
                "optimal": float(data.get("ph_optimal", (ph_min + ph_max) / 2)),
                "source": "farmvillage",
                "scientific_name": data.get("latin_name"),
            }
        except httpx.HTTPStatusError as e:
            logger.warning("FarmVillage HTTP %s for '%s'", e.response.status_code, species_name)
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as e:
            logger.warning("FarmVillage error for '%s': %s", species_name, e)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Gateway (orchestrator)
# ──────────────────────────────────────────────────────────────────────────────

class BotanicalFallbackGateway:
    """
    Fires both external adapters in parallel and returns the first valid result.

    Usage in FastAPI lifespan:
        async with httpx.AsyncClient() as client:
            gateway = BotanicalFallbackGateway(
                TrefleAdapter(os.getenv("TREFLE_API_TOKEN", ""), client),
                FarmVillageAdapter(os.getenv("FARMVILLAGE_API_KEY", ""), client),
            )
            app.state.botanical_gateway = gateway
    """

    def __init__(self, trefle: TrefleAdapter, farmvillage: FarmVillageAdapter):
        self._trefle = trefle
        self._farmvillage = farmvillage

    async def fetch_tolerance(self, species_name: str) -> Optional[dict]:
        """
        Returns the first valid pH tolerance dict, or None if both adapters fail.
        Never raises — caller must handle None gracefully.
        """
        trefle_result, fv_result = await asyncio.gather(
            self._trefle.fetch_ph_tolerance(species_name),
            self._farmvillage.fetch_ph_tolerance(species_name),
            return_exceptions=True,
        )

        # Trefle has priority (more globally accurate taxonomy)
        for result in (trefle_result, fv_result):
            if isinstance(result, dict) and result.get("min") is not None:
                logger.info(
                    "Botanical data for '%s' retrieved from %s",
                    species_name,
                    result.get("source", "unknown"),
                )
                return result

        logger.info(
            "Full cache miss for '%s' — both external sources returned no data.",
            species_name,
        )
        return None
