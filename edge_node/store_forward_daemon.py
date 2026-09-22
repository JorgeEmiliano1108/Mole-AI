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
store_forward_daemon.py — Mole.AI Edge Node
============================================
Runs as a background process on the farmer's laptop/smartphone.

Responsibilities:
  1. Expose enqueue_reading() — called by MQTT subscriber and TFLite runner
  2. Persist readings to local SQLite (works 100% offline)
  3. Authenticate against Supabase Auth (M2M) to obtain a JWT
  4. Push pending records to Django backend in batches when internet is available
  5. Auto-refresh JWT upon 401 Unauthorized (Zero-Trust compliance)

Configuration via .env (nombres genéricos; legacy entre paréntesis):
  IDP_BASE_URL           — URL base del proveedor de identidad GoTrue-compatible
                           (legacy: SUPABASE_URL, ej. https://xxx.supabase.co)
  EDGE_IDENTITY_USER     — email de la cuenta de servicio M2M de este nodo
                           (legacy: EDGE_NODE_EMAIL)
  EDGE_IDENTITY_PASSWORD — password de la cuenta de servicio M2M
                           (legacy: EDGE_NODE_PASSWORD)
  IDP_SERVICE_KEY        — clave de servicio del IdP, header `apikey`
                           (legacy: SUPABASE_KEY)
  EDGE_SYNC_URL          — URL completa de POST /api/v1/sensor-data/edge-batch/
                           (legacy: CLOUD_API_URL, BACKEND_BATCH_URL)
  SYNC_INTERVAL          — segundos entre intentos de sync (default: 30)
  HARDWARE_API_KEY       — fallback legacy (compatibilidad transitoria)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
def _env_first(*names: str, default: str = "") -> str:
    """Primera var definida y no vacía (genérica primero, legacy después)."""
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


DB_PATH = Path(os.getenv("EDGE_DB_PATH", "edge_mole.sqlite3"))

# WAN-ready (ADR-0002: trama edge canónica): EDGE_SYNC_URL → legacy → localhost
BACKEND_BATCH_URL = _env_first(
    "EDGE_SYNC_URL",
    "CLOUD_API_URL",
    "BACKEND_BATCH_URL",
    default="http://localhost:8000/api/v1/sensor-data/edge-batch/",
)
SYNC_INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL", "30"))
MAX_BATCH_SIZE = 200  # Mantiene a salvo tiers gratuitos del IdP/vector DB

# ── IdP M2M Auth (Zero-Trust; GoTrue-compatible) ────────────────────────────
SUPABASE_URL = _env_first("IDP_BASE_URL", "SUPABASE_URL")
EDGE_NODE_EMAIL = _env_first("EDGE_IDENTITY_USER", "EDGE_NODE_EMAIL")
EDGE_NODE_PASSWORD = _env_first("EDGE_IDENTITY_PASSWORD", "EDGE_NODE_PASSWORD")

# ── Legacy fallback (backward compatibility during transition) ───────────────
HARDWARE_API_KEY = os.getenv("HARDWARE_API_KEY", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [EDGE-DAEMON] %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── JWT Token Store ───────────────────────────────────────────────────────────

class _TokenStore:
    """In-memory JWT token store with Supabase Auth refresh capability."""

    def __init__(self) -> None:
        self.access_token: str = ""
        self.refresh_token: str = ""

    async def authenticate(self) -> None:
        """Obtain a fresh JWT from the IdP using email/password grant."""
        if not SUPABASE_URL or not EDGE_NODE_EMAIL or not EDGE_NODE_PASSWORD:
            logger.warning(
                "IdP M2M credentials not configured (IDP_BASE_URL / "
                "EDGE_IDENTITY_USER / EDGE_IDENTITY_PASSWORD). "
                "Falling back to legacy X-Hardware-Api-Key."
            )
            return

        auth_url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password"
        payload = {
            "email": EDGE_NODE_EMAIL,
            "password": EDGE_NODE_PASSWORD,
        }
        headers = {
            "apikey": _env_first("IDP_SERVICE_KEY", "SUPABASE_KEY"),
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(auth_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", "")
        logger.info("Supabase M2M authentication successful.")

    async def refresh(self) -> None:
        """Refresh the JWT using the stored refresh_token."""
        if not self.refresh_token:
            await self.authenticate()
            return

        refresh_url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=refresh_token"
        payload = {"refresh_token": self.refresh_token}
        headers = {
            "apikey": _env_first("IDP_SERVICE_KEY", "SUPABASE_KEY"),
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(refresh_url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            self.access_token = data["access_token"]
            self.refresh_token = data.get("refresh_token", self.refresh_token)
            logger.info("JWT refreshed successfully.")
        except httpx.HTTPError:
            logger.warning("Refresh token expired or invalid. Re-authenticating.")
            await self.authenticate()

    def build_headers(self) -> dict[str, str]:
        """Build HTTP headers for requests to Django backend."""
        headers: dict[str, str] = {}

        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        # Include legacy key as fallback during transition
        if HARDWARE_API_KEY:
            headers["X-Hardware-Api-Key"] = HARDWARE_API_KEY

        return headers


_token_store = _TokenStore()


# ── SQLite setup ──────────────────────────────────────────────────────────────

def init_db() -> sqlite3.Connection:
    """Initialize local SQLite database. Idempotent — safe to call on startup."""
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("""
        CREATE TABLE IF NOT EXISTS pending_readings (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id    TEXT    NOT NULL,
            plant_id     TEXT    NOT NULL,
            timestamp    TEXT    NOT NULL,
            sensors_json TEXT    NOT NULL,
            ph_cnn       REAL,
            synced       INTEGER DEFAULT 0,
            created_at   TEXT    DEFAULT (datetime('now'))
        )
    """)
    # Unique index prevents duplicate records on re-sync
    con.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_device_ts
        ON pending_readings(device_id, timestamp)
    """)
    # Cursor de sincronización JSON-RPC (MRF03): último applied_up_to
    # confirmado por el backend. Tabla kv para no tocar el esquema.
    con.execute("""
        CREATE TABLE IF NOT EXISTS sync_state (
            k TEXT PRIMARY KEY,
            v TEXT NOT NULL
        )
    """)
    con.commit()
    logger.info("SQLite store initialised at %s", DB_PATH)
    return con


def get_cursor(con: sqlite3.Connection) -> str | None:
    """Último `applied_up_to` confirmado (None = sincronización inicial)."""
    row = con.execute(
        "SELECT v FROM sync_state WHERE k='applied_up_to'"
    ).fetchone()
    return row[0] if row else None


def set_cursor(con: sqlite3.Connection, applied_up_to: str | None) -> None:
    if not applied_up_to:
        return
    con.execute(
        "INSERT INTO sync_state(k, v) VALUES('applied_up_to', ?) "
        "ON CONFLICT(k) DO UPDATE SET v=excluded.v",
        (applied_up_to,),
    )
    con.commit()


def enqueue_reading(
    con: sqlite3.Connection,
    device_id: str,
    plant_id: str,
    sensors: dict,
    ph_cnn: float | None = None,
    timestamp: str | None = None,
) -> None:
    """
    Thread-safe. Called by:
      • openclaw_gateway.py       — when ESP32 telemetry arrives
      • inference.py              — after TFLite CNN produces ph_cnn
    """
    ts = timestamp or datetime.now(tz=timezone.utc).isoformat()
    try:
        con.execute(
            "INSERT OR IGNORE INTO pending_readings "
            "(device_id, plant_id, timestamp, sensors_json, ph_cnn) "
            "VALUES (?, ?, ?, ?, ?)",
            (device_id, plant_id, ts, json.dumps(sensors), ph_cnn),
        )
        con.commit()
        logger.debug("Enqueued reading for %s @ %s", device_id, ts)
    except sqlite3.Error as e:
        logger.error("Failed to enqueue reading: %s", e)


# ── Sync loop ─────────────────────────────────────────────────────────────────

async def sync_to_backend(con: sqlite3.Connection) -> None:
    """Push up to MAX_BATCH_SIZE unsynced records to Django backend."""
    rows = con.execute(
        "SELECT id, device_id, plant_id, timestamp, sensors_json, ph_cnn "
        "FROM pending_readings WHERE synced=0 ORDER BY id LIMIT ?",
        (MAX_BATCH_SIZE,),
    ).fetchall()

    if not rows:
        return

    batch = []
    for r in rows:
        sensors_dict = json.loads(r[4])
        entry: dict = {
            "plant_id":  r[2],
            "recorded_at": r[3],
        }
        # Aplanar los sensores (air_temperature, soil_humidity, etc.)
        entry.update(sensors_dict)
        
        # Agregar ph inferido si existe
        if r[5] is not None:
            entry["ph_level"] = r[5]
            
        batch.append(entry)

    ids = [r[0] for r in rows]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                BACKEND_BATCH_URL,
                json={"batch": batch},
                headers=_token_store.build_headers(),
            )

            # Auto-refresh on 401 and retry once
            if resp.status_code == 401:
                logger.warning("Received 401. Refreshing JWT and retrying...")
                await _token_store.refresh()
                resp = await client.post(
                    BACKEND_BATCH_URL,
                    json={"batch": batch},
                    headers=_token_store.build_headers(),
                )

            resp.raise_for_status()
            result = resp.json()

        # Mark as synced only after backend confirmed
        placeholders = ",".join("?" * len(ids))
        con.execute(
            f"UPDATE pending_readings SET synced=1 WHERE id IN ({placeholders})",
            ids,
        )
        con.commit()
        logger.info(
            "Batch synced — sent: %d, registered: %d, skipped: %d",
            len(batch),
            result.get("registered", "?"),
            result.get("skipped_duplicates", "?"),
        )
    except httpx.ConnectError:
        logger.warning("No internet connection. Will retry in %ds.", SYNC_INTERVAL_SECONDS)
    except httpx.HTTPStatusError as e:
        logger.error("Backend rejected batch (%s): %s", e.response.status_code, e.response.text)
    except httpx.HTTPError as e:
        logger.warning("HTTP error during sync: %s", e)


# ── JSON-RPC sync con cursor (MRF03/RNF06, F3, dual-stack) ────────────────
# Opt-in por dispositivo: solo se usa si EDGE_DEVICE_TOKEN (Bearer del
# dispositivo) y EDGE_SYNC_JSONRPC_URL están configurados. Sin ellos, el
# daemon sigue el path legacy intacto. Si el backend responde 404/405/501
# (sin /sync/batch/), se vuelve al legacy automáticamente.
SYNC_JSONRPC_URL = _env_first("EDGE_SYNC_JSONRPC_URL", default="")
EDGE_DEVICE_TOKEN = os.getenv("EDGE_DEVICE_TOKEN", "")


class LegacyBackend(Exception):
    """El backend no expone /sync/batch/: usar path legacy."""


def build_frame_from_row(row) -> dict | None:
    """Convierte fila legacy (id, device_id, plant_id, timestamp ISO,
    sensors_json, ph_cnn) a trama edge `{ts, ri, a}`.

    Limitación honesta: las filas legacy no guardan pin de suelo, por lo que
    `s` va vacío (el suelo requiere enqueue con pin — futuro). `ts` en epoch.
    Retorna None si la fila no es convertible.
    """
    try:
        sensors = json.loads(row[4]) if row[4] else {}
        ts = datetime.fromisoformat(str(row[3]).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        frame: dict = {
            "ts": ts.timestamp(),
            "ri": 5,
        }
        ambient = {}
        if sensors.get("air_temperature") is not None:
            ambient["t"] = float(sensors["air_temperature"])
        if sensors.get("air_humidity") is not None:
            ambient["h"] = float(sensors["air_humidity"])
        if sensors.get("light_level") is not None:
            ambient["l"] = float(sensors["light_level"])
        if sensors.get("uv_index") is not None:
            ambient["u"] = float(sensors["uv_index"])
        if ambient:
            frame["a"] = ambient
        frame["s"] = []
        return frame
    except (ValueError, TypeError, KeyError, OverflowError, OSError):
        return None


async def sync_jsonrpc(con: sqlite3.Connection) -> str:
    """Sincroniza pendientes vía JSON-RPC `sync.telemetry` con cursor.

    Retorna `applied_up_to` confirmado. Marca `synced=1` solo los aceptados
    y persiste el cursor. Lanza `LegacyBackend` si el backend no conoce la
    ruta; otros fallos HTTP se propagan para reintento posterior.
    """
    import uuid

    rows = con.execute(
        "SELECT id, device_id, plant_id, timestamp, sensors_json, ph_cnn "
        "FROM pending_readings WHERE synced=0 ORDER BY id LIMIT ?",
        (MAX_BATCH_SIZE,),
    ).fetchall()
    if not rows:
        return get_cursor(con) or ""

    frames, ids = [], []
    for r in rows:
        frame = build_frame_from_row(r)
        if frame is None:
            continue
        frames.append(frame)
        ids.append(r[0])
    if not frames:
        return get_cursor(con) or ""

    envelope = {
        "jsonrpc": "2.0",
        "method": "sync.telemetry",
        "params": {"cursor": get_cursor(con), "frames": frames},
        "id": f"edge-{uuid.uuid4().hex[:8]}",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            SYNC_JSONRPC_URL,
            json=envelope,
            headers={"Authorization": f"Bearer {EDGE_DEVICE_TOKEN}"},
        )
    if resp.status_code in (404, 405, 501):
        raise LegacyBackend(f"backend sin /sync/batch/ ({resp.status_code})")
    resp.raise_for_status()
    body = resp.json()
    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
        raise ValueError("Respuesta no JSON-RPC 2.0")
    if "error" in body:
        err = body["error"] or {}
        raise RuntimeError(f"sync rechazado {err.get('code')}: {err.get('message')}")
    result = body.get("result", {}) or {}
    accepted_idx = set(result.get("accepted", []) or [])
    done_ids = [ids[i] for i in accepted_idx if 0 <= i < len(ids)]
    if done_ids:
        placeholders = ",".join("?" * len(done_ids))
        con.execute(
            f"UPDATE pending_readings SET synced=1 WHERE id IN ({placeholders})",
            done_ids,
        )
        con.commit()
    applied = result.get("applied_up_to")
    set_cursor(con, applied)
    logger.info(
        "JSON-RPC sync — enviadas: %d, aceptadas: %d, cursor: %s",
        len(frames), len(done_ids), applied,
    )
    return applied or ""


async def main() -> None:
    con = init_db()

    # Attempt initial M2M authentication against Supabase
    try:
        await _token_store.authenticate()
    except Exception as exc:
        logger.warning(
            "Initial Supabase auth failed (%s). Will use legacy key and retry later.",
            exc,
        )

    logger.info(
        "Daemon started. Syncing every %ds → %s",
        SYNC_INTERVAL_SECONDS,
        BACKEND_BATCH_URL,
    )
    use_jsonrpc = bool(SYNC_JSONRPC_URL and EDGE_DEVICE_TOKEN)
    if use_jsonrpc:
        logger.info("JSON-RPC sync habilitado → %s", SYNC_JSONRPC_URL)
    while True:
        if use_jsonrpc:
            try:
                await sync_jsonrpc(con)
            except LegacyBackend as exc:
                logger.warning("%s Volviendo a legacy.", exc)
                use_jsonrpc = False
                await sync_to_backend(con)
            except (httpx.HTTPError, RuntimeError, ValueError) as exc:
                logger.warning("JSON-RPC sync falló (%s). Reintento luego.", exc)
        else:
            await sync_to_backend(con)
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
