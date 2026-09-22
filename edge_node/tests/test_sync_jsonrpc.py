"""Daemon JSON-RPC F3 (MRF03): cursor, envelope, fallback legacy.

Sin red ni broker: `httpx` mockeado a nivel transporte, SQLite temporal.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import store_forward_daemon as sfd


@pytest.fixture
def con(tmp_path, monkeypatch):
    monkeypatch.setattr(sfd, "DB_PATH", tmp_path / "t.sqlite3")
    return sfd.init_db()


def _row(ts="2026-09-01T10:00:00+00:00", sensors=None, ph=None):
    return (1, "dev-1", "plant-1", ts,
            json.dumps(sensors or {"air_temperature": 23.5}), ph)


class TestFrameBuilder:
    def test_mapea_sensores_conocidos(self):
        f = sfd.build_frame_from_row(_row())
        assert f["a"] == {"t": 23.5}
        assert f["s"] == []
        assert f["ri"] == 5
        assert abs(f["ts"] - 1788256800.0) < 1  # 2026-09-01T10:00:00Z

    def test_fila_ilegible_none(self):
        assert sfd.build_frame_from_row((1, "d", "p", "no-fecha", "{}", None)) is None


class FakeResp:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError("e", request=None, response=self)

    def json(self):
        return self._payload


def _seed(con, n=2):
    for i in range(n):
        con.execute(
            "INSERT INTO pending_readings(device_id, plant_id, timestamp, sensors_json, ph_cnn, synced)"
            " VALUES(?,?,?,?,?,0)",
            ("dev-1", "plant-1", f"2026-09-01T10:{i:02d}:00+00:00",
             json.dumps({"air_temperature": 20.0 + i}), None),
        )
    con.commit()


@pytest.mark.anyio
async def test_jsonrpc_aplica_cursor_y_marca(con, monkeypatch):
    _seed(con)
    monkeypatch.setattr(sfd, "SYNC_JSONRPC_URL", "http://x/api/v1/sync/batch/")
    monkeypatch.setattr(sfd, "EDGE_DEVICE_TOKEN", "tok")

    async def fake_post(self, url, json=None, headers=None):
        assert json["jsonrpc"] == "2.0"
        assert json["method"] == "sync.telemetry"
        assert headers["Authorization"] == "Bearer tok"
        assert len(json["params"]["frames"]) == 2
        return FakeResp(200, {"jsonrpc": "2.0",
                              "result": {"applied_up_to": "2026-09-01T10:01:00+00:00",
                                         "accepted": [0, 1], "conflicts": []},
                              "id": json["id"]})

    import httpx
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    applied = await sfd.sync_jsonrpc(con)
    assert applied == "2026-09-01T10:01:00+00:00"
    assert sfd.get_cursor(con) == applied
    left = con.execute(
        "SELECT COUNT(*) FROM pending_readings WHERE synced=0").fetchone()[0]
    assert left == 0


@pytest.mark.anyio
async def test_jsonrpc_404_fallback_legacy(con, monkeypatch):
    _seed(con)
    monkeypatch.setattr(sfd, "SYNC_JSONRPC_URL", "http://x/api/v1/sync/batch/")
    monkeypatch.setattr(sfd, "EDGE_DEVICE_TOKEN", "tok")

    async def fake_post(self, url, json=None, headers=None):
        return FakeResp(404, {})

    import httpx
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    with pytest.raises(sfd.LegacyBackend):
        await sfd.sync_jsonrpc(con)
    # Nada marcado: el path legacy lo reintentará.
    left = con.execute(
        "SELECT COUNT(*) FROM pending_readings WHERE synced=0").fetchone()[0]
    assert left == 2


def test_cursor_roundtrip(con):
    assert sfd.get_cursor(con) is None
    sfd.set_cursor(con, "2026-09-01T10:00:00+00:00")
    assert sfd.get_cursor(con) == "2026-09-01T10:00:00+00:00"
    sfd.set_cursor(con, None)  # no-op, no borra
    assert sfd.get_cursor(con) == "2026-09-01T10:00:00+00:00"
