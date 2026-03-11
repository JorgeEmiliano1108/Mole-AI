"""
mqtt_local_subscriber.py — Mole.AI Edge Node
=============================================
Subscribes to the ESP32's local MQTT broker (LAN only, no internet required).
Enqueues every received telemetry message into local SQLite for later sync.

Expected MQTT topic:  mole/sensors/<device_id>
Expected payload:
{
  "device_id": "ESP32-001",
  "plant_id":  "planta_maiz_01",
  "sensors": [
    {"type": "temperature", "value": 27.4, "unit": "C"},
    {"type": "humidity",    "value": 62.0, "unit": "%"}
  ],
  "timestamp": "2026-03-07T10:30:00"   # optional
}

Run alongside store_forward_daemon.py:
  python mqtt_local_subscriber.py &
  python store_forward_daemon.py
"""
from __future__ import annotations

import json
import logging
import os

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from store_forward_daemon import enqueue_reading, init_db

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
MQTT_BROKER_HOST = os.getenv("MQTT_LOCAL_HOST", "192.168.1.1")
MQTT_PORT = int(os.getenv("MQTT_LOCAL_PORT", "1883"))
TOPIC_SENSOR = "mole/sensors/#"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MQTT-SUB] %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

con = init_db()


# ── MQTT callbacks ─────────────────────────────────────────────────────────────

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        logger.info("Connected to local MQTT broker at %s:%d", MQTT_BROKER_HOST, MQTT_PORT)
        client.subscribe(TOPIC_SENSOR)
        logger.info("Subscribed to topic: %s", TOPIC_SENSOR)
    else:
        logger.error("MQTT connection refused — reason code %s", reason_code)


def on_disconnect(client, userdata, flags, reason_code, properties=None):
    logger.warning("Disconnected from MQTT broker (code %s). Reconnecting...", reason_code)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        device_id = payload.get("device_id") or msg.topic.split("/")[-1]
        plant_id = payload.get("plant_id", "unknown")
        sensors = payload.get("sensors", [])
        timestamp = payload.get("timestamp")

        if not sensors:
            logger.warning("Received empty sensors list from %s — skipping.", device_id)
            return

        enqueue_reading(
            con,
            device_id=device_id,
            plant_id=plant_id,
            sensors=sensors,
            timestamp=timestamp,
        )
        logger.debug("Enqueued %d sensors from %s", len(sensors), device_id)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON on topic %s: %s", msg.topic, e)
    except KeyError as e:
        logger.error("Missing field in payload from %s: %s", msg.topic, e)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    logger.info("Connecting to local MQTT broker %s:%d...", MQTT_BROKER_HOST, MQTT_PORT)
    client.connect(MQTT_BROKER_HOST, MQTT_PORT, keepalive=60)
    client.loop_forever()
