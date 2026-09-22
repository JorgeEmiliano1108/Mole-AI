"""Sync JSON-RPC con cursor F3 (MRF03/RNF06) + refactor edge-batch sin regresión.

- `POST /api/v1/sync/batch/` envelope estricto, cursor, idempotencia.
- `POST /api/v1/sensor-data/edge-batch/` legacy intacto tras el refactor
  a servicio compartido (`apps/core/services/edge_ingest.py`).
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from apps.core.models import AmbientReading, Device, HardwareBinding, SoilReading
from apps.plants.models import UserPlant


# Sin Redis local el middleware de degradación responde 503 (issue 10);
# locmem aísla estos tests de infraestructura.
@pytest.fixture(autouse=True)
def _locmem_cache():
    with override_settings(CACHES={
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }):
        yield

User = get_user_model()
TS = 1700000000.0  # pasado fijo (anti-replay solo rechaza futuro +5min)


@pytest.fixture
def rig(db):
    user = User.objects.create_user(username="edge1", password="x")
    plant = UserPlant.objects.create(user=user, nickname="P1")
    device = Device.objects.create(
        owner=user, name="esp32-1", auth_token="tok-edge-1", status="offline"
    )
    HardwareBinding.objects.create(device=device, hardware_pin="34", plant=plant)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer tok-edge-1")
    return client, device


def _frame(ts=TS, pin="34", v=2048, extra=None):
    f = {"ts": ts, "ri": 5,
         "a": {"t": 23.5, "h": 55.0, "l": 12000, "u": 3.0},
         "s": [{"p": pin, "v": v}]}
    if extra:
        f.update(extra)
    return f


def _rpc(frames, method="sync.telemetry", rid="e2e-1", cursor=None):
    return {"jsonrpc": "2.0", "method": method,
            "params": {"cursor": cursor, "frames": frames}, "id": rid}


@pytest.mark.django_db
class TestSyncBatch:
    def test_happy_path_aplica_cursor(self, rig):
        client, device = rig
        resp = client.post("/api/v1/sync/batch/",
                           _rpc([_frame(), _frame(ts=TS + 60)]), format="json")
        assert resp.status_code == 200, resp.content[:200]
        body = resp.json()
        assert body["jsonrpc"] == "2.0" and body["id"] == "e2e-1"
        result = body["result"]
        assert result["accepted"] == [0, 1]
        assert result["conflicts"] == []
        assert result["applied_up_to"] is not None
        assert AmbientReading.objects.filter(device=device).count() == 2
        assert SoilReading.objects.count() == 2

    def test_reenvio_idempotente(self, rig):
        client, device = rig
        payload = _rpc([_frame()])
        assert client.post("/api/v1/sync/batch/", payload, format="json").status_code == 200
        resp = client.post("/api/v1/sync/batch/", payload, format="json")
        assert resp.json()["result"]["accepted"] == [0]
        assert AmbientReading.objects.filter(device=device).count() == 1
        assert SoilReading.objects.count() == 1

    def test_frame_invalida_conflicto_y_resto_ok(self, rig):
        client, device = rig
        bad = {"ts": "no-epoch", "s": []}
        resp = client.post("/api/v1/sync/batch/",
                           _rpc([bad, _frame()]), format="json")
        body = resp.json()
        assert body["result"]["accepted"] == [1]
        assert body["result"]["conflicts"][0]["index"] == 0
        assert AmbientReading.objects.filter(device=device).count() == 1

    def test_pin_huerfano_conflicto_parcial(self, rig):
        client, device = rig
        resp = client.post("/api/v1/sync/batch/",
                           _rpc([_frame(pin="99")]), format="json")
        body = resp.json()
        # Trama válida pero pin sin binding: se acepta con soil_mapped=0
        # (A1); el pin huérfano no es conflicto de protocolo.
        assert body["result"]["accepted"] == [0]
        assert SoilReading.objects.count() == 0
        assert AmbientReading.objects.filter(device=device).count() == 1

    def test_sin_auth_401(self, rig):
        resp = APIClient().post("/api/v1/sync/batch/",
                                _rpc([_frame()]), format="json")
        assert resp.status_code == 401

    def test_envelope_invalido(self, rig):
        client, _ = rig
        r = client.post("/api/v1/sync/batch/", {"method": "x"}, format="json")
        assert r.json()["error"]["code"] == -32600
        assert r.json()["id"] is None  # id ausente → null (JSON-RPC 2.0)

    def test_metodo_desconocido(self, rig):
        client, _ = rig
        r = client.post("/api/v1/sync/batch/",
                        _rpc([], method="otro.metodo", rid="z9"), format="json")
        assert r.json()["error"]["code"] == -32601
        assert r.json()["id"] == "z9"

    def test_params_invalidos(self, rig):
        client, _ = rig
        r = client.post("/api/v1/sync/batch/",
                        {"jsonrpc": "2.0", "method": "sync.telemetry",
                         "params": {}, "id": 7}, format="json")
        assert r.json()["error"]["code"] == -32602
        assert r.json()["id"] == 7


@pytest.mark.django_db
class TestEdgeBatchLegacyIntacto:
    def test_happy_path_igual_que_antes(self, rig):
        client, device = rig
        resp = client.post("/api/v1/sensor-data/edge-batch/",
                           _frame(), format="json")
        assert resp.status_code == 200, resp.content[:200]
        body = resp.json()
        assert body == {"status": "ingested", "ambient": True,
                        "soil_mapped": 1, "orphaned_pins": []}
        assert AmbientReading.objects.filter(device=device).count() == 1
        assert SoilReading.objects.count() == 1
