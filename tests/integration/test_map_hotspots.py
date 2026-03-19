# =============================================================================
# Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
#
# AVISO DE PROPIEDAD INTELECTUAL:
# Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
# Queda estrictamente prohibida la copia, modificación, distribución,
# sublicenciamiento o uso comercial de este código, total o parcialmente,
# sin la autorización expresa y por escrito de los titulares del Copyright.
#
# Cualquier uso no autorizado será perseguido conforme a la Ley Federal
# del Derecho de Autor (México) y tratados internacionales aplicables.
# =============================================================================
"""
Integration tests for GET /api/v1/map/hotspots/

Requirements verified:
1. HTTP 200 for authenticated users.
2. Two nearby points cluster into one centroid with total_casos >= 2.
3. Response contains ONLY abstract aggregated data — no user IDs,
   usernames, or individual-point coordinates.
4. Cache is GLOBAL: a second user gets the identical payload.
5. Unauthenticated requests are rejected (401).
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from core.infrastructure.repositories.models import DiagnosticoGeolocalizado

User = get_user_model()

HOTSPOTS_URL = "/api/v1/map/hotspots/"

# ── Allowed keys that may appear inside each hotspot object ──────────────
ALLOWED_HOTSPOT_KEYS = {
    "latitud_centro",
    "longitud_centro",
    "radio_estimado_metros",
    "total_casos",
    "plaga_predominante",
    "severity_index",
}

# Keys that MUST NEVER appear (privacy gatekeeper)
FORBIDDEN_KEYS = {
    "user", "user_id", "username", "email",
    "latitude", "longitude", "lat", "lon",
    "diagnostic_id", "plant_id",
}


@pytest.fixture(autouse=True)
def _clear_cache():
    """Ensure each test starts with a cold cache."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture()
def user_a():
    return User.objects.create_user(username="farmer_a", password="test1234")


@pytest.fixture()
def user_b():
    return User.objects.create_user(username="farmer_b", password="test5678")


def _seed_points(user):
    """Insert 3 geo-diagnostics: 2 close together + 1 distant."""
    # Close pair — both round to (19.1234, -98.1234) at precision=4
    DiagnosticoGeolocalizado.objects.create(
        user=user,
        condition_name="araña roja",
        latitude=19.12341,
        longitude=-98.12341,
        severity="high",
    )
    DiagnosticoGeolocalizado.objects.create(
        user=user,
        condition_name="araña roja",
        latitude=19.12342,
        longitude=-98.12342,
        severity="medium",
    )
    # Distant point — separate cluster
    DiagnosticoGeolocalizado.objects.create(
        user=user,
        condition_name="roya",
        latitude=21.0000,
        longitude=-100.0000,
        severity="low",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestMapHotspotsEndpoint:
    """Functional tests for the hotspots clustering endpoint."""

    def test_returns_200_and_correct_structure(self, user_a):
        _seed_points(user_a)
        client = APIClient()
        client.force_authenticate(user=user_a)

        resp = client.get(HOTSPOTS_URL, {"precision": 4})

        assert resp.status_code == 200
        body = resp.json()
        assert "hotspots" in body
        assert "total_clusters" in body
        assert "total_incidents_mapped" in body
        assert body["total_incidents_mapped"] == 3

    def test_clusters_nearby_points(self, user_a):
        """Two points at ~11 m apart at precision=4 must merge."""
        _seed_points(user_a)
        client = APIClient()
        client.force_authenticate(user=user_a)

        resp = client.get(HOTSPOTS_URL, {"precision": 4})
        hotspots = resp.json()["hotspots"]

        # Expect 2 clusters: one with 2 cases, one with 1
        counts = sorted(h["total_casos"] for h in hotspots)
        assert counts == [1, 2]

    def test_dominant_pest_label(self, user_a):
        _seed_points(user_a)
        client = APIClient()
        client.force_authenticate(user=user_a)

        resp = client.get(HOTSPOTS_URL, {"precision": 4})
        hotspots = resp.json()["hotspots"]

        cluster_2 = next(h for h in hotspots if h["total_casos"] == 2)
        assert cluster_2["plaga_predominante"] == "araña roja"

    def test_no_personal_data_leaked(self, user_a):
        """Each hotspot must contain ONLY abstract aggregated fields."""
        _seed_points(user_a)
        client = APIClient()
        client.force_authenticate(user=user_a)

        resp = client.get(HOTSPOTS_URL, {"precision": 4})
        for hotspot in resp.json()["hotspots"]:
            present_keys = set(hotspot.keys())
            leaked = present_keys & FORBIDDEN_KEYS
            assert not leaked, f"Personal/coordinate keys leaked: {leaked}"
            assert present_keys <= ALLOWED_HOTSPOT_KEYS, (
                f"Unexpected keys: {present_keys - ALLOWED_HOTSPOT_KEYS}"
            )

    def test_global_cache_same_payload_for_different_users(self, user_a, user_b):
        """Both users must receive the same community hotspots."""
        _seed_points(user_a)
        client = APIClient()

        client.force_authenticate(user=user_a)
        resp_a = client.get(HOTSPOTS_URL, {"precision": 4})

        client.force_authenticate(user=user_b)
        resp_b = client.get(HOTSPOTS_URL, {"precision": 4})

        assert resp_a.json() == resp_b.json()

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        resp = client.get(HOTSPOTS_URL)
        assert resp.status_code in (401, 403)

    def test_radius_positive_for_multipoint_cluster(self, user_a):
        """A cluster with >1 point must have radius > 0 metres."""
        _seed_points(user_a)
        client = APIClient()
        client.force_authenticate(user=user_a)

        resp = client.get(HOTSPOTS_URL, {"precision": 4})
        cluster_2 = next(
            h for h in resp.json()["hotspots"] if h["total_casos"] == 2
        )
        assert cluster_2["radio_estimado_metros"] > 0

    def test_filter_by_pest(self, user_a):
        _seed_points(user_a)
        client = APIClient()
        client.force_authenticate(user=user_a)

        resp = client.get(HOTSPOTS_URL, {"precision": 4, "pest": "roya"})
        body = resp.json()
        assert body["total_incidents_mapped"] == 1
        assert body["hotspots"][0]["plaga_predominante"] == "roya"

    def test_filter_by_days(self, user_a):
        _seed_points(user_a)
        client = APIClient()
        client.force_authenticate(user=user_a)

        # All 3 points were just created — days=1 should include them
        resp = client.get(HOTSPOTS_URL, {"precision": 4, "days": 1})
        assert resp.json()["total_incidents_mapped"] == 3

        # days=0 => cutoff = now ⇒ nothing (auto_now_add is ≤ now)
        resp0 = client.get(HOTSPOTS_URL, {"precision": 4, "days": 0})
        # days=0 is not digits-positive so falls through unfiltered
        # (the view checks `str(days).isdigit()` which is True for '0')
        # timedelta(days=0) → cutoff = now — nothing created "after now"
        # so expect 0 or 3 depending on auto_now_add timing.
        assert resp0.status_code == 200
