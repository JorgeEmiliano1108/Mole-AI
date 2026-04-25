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
openclaw_gateway.py — Mole.AI Edge Node OpenClaw Gateway
=========================================================
Replaces mqtt_local_subscriber.py for ESP32 nodes running OpenClaw firmware.

This script acts as a lightweight OpenClaw Gateway, accepting WebSocket
connections from ESP32 nodes, processing the OpenClaw protocol handshake,
and forwarding telemetry data into the local SQLite store-and-forward queue.
"""
import asyncio
import json
import logging
import websockets
from websockets.exceptions import ConnectionClosed
from store_forward_daemon import enqueue_reading, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [OPENCLAW-GW] %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

con = init_db()

# Mapeo Simulado (Zero-Trust Identity a Django UUID)
# En producción, esto se consultaría a la BD o caché (Redis).
DEVICE_TO_PLANT_MAP = {
    # Ejemplo de Ed25519 PubKey Hex : Plant UUID
    "d4b3c2a1f0e9d8c7b6a594837261504f": "123e4567-e89b-12d3-a456-426614174000",
}
DEFAULT_PLANT_ID = "00000000-0000-0000-0000-000000000000"


async def handle_node(ws: websockets.WebSocketServerProtocol):
    peer = ws.remote_address
    node_name = f"unknown-{peer[0]}:{peer[1]}"
    logger.info(f"New connection from {peer}")

    try:
        async for raw_message in ws:
            try:
                frame = json.loads(raw_message)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {node_name}")
                continue

            msg_type = frame.get("type")
            method = frame.get("method")
            params = frame.get("params", {})
            msg_id = frame.get("id", "")

            if msg_type == "req" and method == "connect":
                # Handshake y captura de identidad
                node_name = params.get("node_name", node_name)
                logger.info(f"Node connected: {node_name}")
                await ws.send(json.dumps({"type": "res", "id": msg_id, "result": "connected"}))
            
            elif msg_type == "req" and method == "telemetry.report":
                timestamp = params.get("timestamp")
                if not timestamp:
                    logger.warning(f"Rejecting telemetry from {node_name}: no timestamp")
                    await ws.send(json.dumps({
                        "type": "res", "id": msg_id, 
                        "error": {"code": 400, "message": "timestamp required"}
                    }))
                    continue
                
                # Aplanamiento del JSON al contrato del Backend (SensorBatchReadingSerializer)
                flattened_sensors = {
                    "air_temperature": params.get("temperature_c"),
                    "air_humidity": params.get("humidity_pct"),
                    "soil_humidity": params.get("soil_moisture_pct"),
                    "light_level": params.get("light_lux"),
                    "uv_index": params.get("uv_index"),
                }
                
                # Remover nulos
                flattened_sensors = {k: v for k, v in flattened_sensors.items() if v is not None}
                
                # Resolver Plant ID
                plant_id = DEVICE_TO_PLANT_MAP.get(node_name, DEFAULT_PLANT_ID)
                
                if flattened_sensors:
                    # Llamada al Store & Forward con JSON aplanado
                    enqueue_reading(
                        con=con,
                        device_id=node_name,
                        plant_id=plant_id,
                        sensors=flattened_sensors, # ¡Ahora es un dict plano, no una lista!
                        timestamp=timestamp
                    )
                    logger.info(f"Enqueued telemetry from {node_name} @ {timestamp}")
                
                await ws.send(json.dumps({"type": "res", "id": msg_id, "result": "accepted"}))

            elif msg_type == "res":
                # Respuestas a comandos como heartbeat, no requiere acción
                pass

    except ConnectionClosed:
        logger.info(f"Node {node_name} disconnected")
    except Exception as e:
        logger.error(f"Error handling node {node_name}: {e}")

async def main():
    logger.info("Starting OpenClaw Gateway on 0.0.0.0:18789")
    async with websockets.serve(handle_node, "0.0.0.0", 18789):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
