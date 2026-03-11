"""
store_forward_daemon.py — Mole.AI Edge Node
============================================
Runs as a background process on the farmer's laptop/smartphone.

Responsibilities:
  1. Expose enqueue_reading() — called by MQTT subscriber and TFLite runner
  2. Persist readings to local SQLite (works 100% offline)
  3. Push pending records to Django backend in batches when internet is available

Configuration via .env:
  HARDWARE_API_KEY   — same key as Django HARDWARE_API_KEY setting
  BACKEND_BATCH_URL  — full URL of POST /api/v1/sensor-data/batch/
  SYNC_INTERVAL      — seconds between sync attempts (default: 30)
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
DB_PATH = Path(os.getenv("EDGE_DB_PATH", "edge_mole.sqlite3"))
BACKEND_BATCH_URL = os.getenv(
    "BACKEND_BATCH_URL",
    "http://localhost:8000/api/v1/sensor-data/batch/",
)
SYNC_INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL", "30"))
HARDWARE_API_KEY = os.getenv("HARDWARE_API_KEY", "")
MAX_BATCH_SIZE = 200  # Keep Supabase free tier safe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [EDGE-DAEMON] %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


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
    con.commit()
    logger.info("SQLite store initialised at %s", DB_PATH)
    return con


def enqueue_reading(
    con: sqlite3.Connection,
    device_id: str,
    plant_id: str,
    sensors: list[dict],
    ph_cnn: float | None = None,
    timestamp: str | None = None,
) -> None:
    """
    Thread-safe. Called by:
      • mqtt_local_subscriber.py  — when ESP32 telemetry arrives
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
        entry: dict = {
            "device_id": r[1],
            "plant_id":  r[2],
            "timestamp": r[3],
            "sensors":   json.loads(r[4]),
        }
        if r[5] is not None:
            entry["ph_cnn"] = r[5]
        batch.append(entry)

    ids = [r[0] for r in rows]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                BACKEND_BATCH_URL,
                json={"batch": batch},
                headers={"X-Hardware-Api-Key": HARDWARE_API_KEY},
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


async def main() -> None:
    con = init_db()
    logger.info(
        "Daemon started. Syncing every %ds → %s",
        SYNC_INTERVAL_SECONDS,
        BACKEND_BATCH_URL,
    )
    while True:
        await sync_to_backend(con)
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
