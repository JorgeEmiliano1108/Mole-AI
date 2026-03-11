"""
Supabase Knowledge Repository — Concrete adapter for Capa Cero.

Uses httpx (already a dependency) to call the Supabase REST API directly.
No extra SDK needed — just SUPABASE_URL + SUPABASE_KEY env vars.

Table used: species_catalog (pre-existing schema)
Relevant columns:
    scientific_name   TEXT  (UNIQUE, non-nullable — used as lookup key)
    ideal_ph_min      FLOAT8
    ideal_ph_max      FLOAT8
    ideal_ph_optimal  FLOAT8
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from domain.ports.knowledge_repository_port import KnowledgeRepositoryPort

logger = logging.getLogger(__name__)


class SupabaseKnowledgeRepo(KnowledgeRepositoryPort):
    """Reads/writes pH tolerance columns in species_catalog via Supabase PostgREST."""

    def __init__(self, supabase_url: str, supabase_key: str, http_client: httpx.AsyncClient):
        self._base = supabase_url.rstrip("/")
        self._headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        self._http = http_client

    # ── Port methods ───────────────────────────────────────────────────────

    async def get_ph_tolerance(self, species: str) -> Optional[dict]:
        """SELECT ideal_ph_min/max/optimal FROM species_catalog WHERE scientific_name = ?"""
        url = (
            f"{self._base}/rest/v1/species_catalog"
            f"?scientific_name=eq.{httpx.QueryParams({'': species}).get('')}"
            f"&select=ideal_ph_min,ideal_ph_max,ideal_ph_optimal"
            f"&limit=1"
        )
        try:
            resp = await self._http.get(url, headers=self._headers, timeout=5.0)
            resp.raise_for_status()
            rows = resp.json()
            if not rows:
                return None
            row = rows[0]
            # Guard: ALL three columns must be non-NULL
            ph_min = row.get("ideal_ph_min")
            ph_max = row.get("ideal_ph_max")
            ph_opt = row.get("ideal_ph_optimal")
            if ph_min is None or ph_max is None or ph_opt is None:
                return None
            return {
                "min": float(ph_min),
                "max": float(ph_max),
                "optimal": float(ph_opt),
            }
        except (httpx.HTTPStatusError, TypeError, ValueError) as exc:
            logger.warning("Supabase GET failed: %s", exc)
            return None

    async def save_ph_tolerance(self, species: str, data: dict) -> None:
        """UPSERT pH columns in species_catalog (idempotent via ON CONFLICT scientific_name)."""
        url = f"{self._base}/rest/v1/species_catalog"
        headers = {
            **self._headers,
            # PostgREST upsert: merge on the UNIQUE column `scientific_name`
            "Prefer": "resolution=merge-duplicates,return=representation",
        }
        ph_min = data.get("min")
        ph_max = data.get("max")
        if ph_min is None or ph_max is None:
            raise ValueError(f"Missing min/max in tolerance data for '{species}': {data}")
        payload = {
            "scientific_name": species,
            "ideal_ph_min": float(ph_min),
            "ideal_ph_max": float(ph_max),
            "ideal_ph_optimal": float(data.get("optimal", (ph_min + ph_max) / 2)),
        }
        try:
            resp = await self._http.post(url, json=payload, headers=headers, timeout=5.0)
            resp.raise_for_status()
            logger.info("Persisted pH tolerance for '%s' to species_catalog.", species)
        except httpx.HTTPStatusError as exc:
            logger.error("Supabase UPSERT failed (%s): %s", exc.response.status_code, exc)
            raise
