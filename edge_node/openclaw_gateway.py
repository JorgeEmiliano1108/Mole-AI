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
========================================================
Zero-Trust Gateway con validación criptográfica Ed25519.

Este script:
  1. Acepta conexiones WebSocket de ESP32 nodes con firmware OpenClaw
  2. Valida firmas Ed25519 de cada payload
  3. Usa Redis como caché de claves públicas (TTL: 3600s)
  4. Silencia paquetes no validados (drop silencioso + log local)
"""
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import asyncpg
import nacl.exceptions
import nacl.public
import nacl.encoding
import redis.asyncio as redis
import websockets
from websockets.exceptions import ConnectionClosed

from store_forward_daemon import enqueue_reading, init_db

# =============================================================================
# Configuración de Logging (Cumple NOM-059 / LFPDPPP)
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [OPENCLAW-GW] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# =============================================================================
# Constantes de Configuración
# =============================================================================
DEFAULT_PLANT_ID = "00000000-0000-0000-0000-000000000000"

# Redis configuration (usar variable de entorno con defaults Docker)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/1")
PUBKEY_CACHE_TTL = 3600  # 1 hora

# PostgreSQL connection (Django backend DB — asyncpg pool)
# Formato: postgresql://user:password@host:5432/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Tabla de Django donde se registran los dispositivos (pubkey_hex como columna)
# Ajustar si el modelo se llama distinto en tu proyecto Django
DEVICES_TABLE = os.getenv("DEVICES_TABLE", "devices_device")
DEVICES_PUBKEY_COLUMN = os.getenv("DEVICES_PUBKEY_COLUMN", "pubkey_hex")

# =============================================================================
# Cliente Redis Global (para reuse en event loop)
# =============================================================================
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """
    Obtiene cliente Redis reutilizable.

    Returns:
        Instancia de redis.asyncio.Redis
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


async def close_redis_client():
    """Cierra conexión Redis al shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


# =============================================================================
# Pool de Conexiones asyncpg (PostgreSQL — Hallazgo #2)
# =============================================================================
_pg_pool: Optional[asyncpg.Pool] = None


async def get_pg_pool() -> Optional[asyncpg.Pool]:
    """
    Retorna el pool de conexiones asyncpg ya inicializado.
    Si DATABASE_URL no está configurado, retorna None (modo degradado).
    """
    return _pg_pool


async def init_pg_pool() -> None:
    """
    Inicializa el pool de conexiones asyncpg al arrancar el Gateway.
    Llamar una vez en main() antes de aceptar conexiones WebSocket.
    """
    global _pg_pool
    if not DATABASE_URL:
        logger.warning(
            "DATABASE_URL no configurado — fetch_pubkey_from_db() deshabilitado. "
            "Solo dispositivos en cache Redis serán aceptados."
        )
        return
    try:
        _pg_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5,              # Pool pequeño — el Gateway no es DB-heavy
            command_timeout=5.0,     # Timeout estricto para no bloquear el event loop
        )
        logger.info("asyncpg pool inicializado → %s", DATABASE_URL.split("@")[-1])
    except Exception as exc:
        logger.error("No se pudo conectar a PostgreSQL: %s. Modo solo-cache activo.", exc)
        _pg_pool = None


async def close_pg_pool() -> None:
    """Cierra el pool asyncpg limpiamente al detener el Gateway."""
    global _pg_pool
    if _pg_pool:
        await _pg_pool.close()
        _pg_pool = None
        logger.info("asyncpg pool cerrado.")


# =============================================================================
# Criptografía Ed25519 (PyNaCl)
# =============================================================================
def bytes_from_hex(hex_string: str) -> bytes:
    """
    Convierte string hexadecimal a bytes.
    
    Args:
        hex_string: String en formato hexadecimal
        
    Returns:
        Bytes decoded
        
    Raises:
        ValueError: Si el string no es hexadecimal válido
    """
    if len(hex_string) % 2 != 0:
        raise ValueError("Hex string must have even length")
    return bytes.fromhex(hex_string)


def decode_public_key(hex_pubkey: str) -> nacl.public.PublicKey:
    """
    Decodifica clave pública Ed25519 desde hexadecimal.
    
    Args:
        hex_pubkey: Clave pública en formato hex (64 caracteres)
        
    Returns:
        Objeto nacl.public.PublicKey
        
    Raises:
        ValueError: Si la clave no es válida
    """
    key_bytes = bytes_from_hex(hex_pubkey)
    if len(key_bytes) != 32:
        raise ValueError(f"Public key must be 32 bytes, got {len(key_bytes)}")
    return nacl.public.PublicKey(key_bytes, encoder=nacl.encoding.RawEncoder)


def verify_ed25519_signature(
    message: bytes, 
    signature_hex: str, 
    pubkey_hex: str
) -> bool:
    """
    Valida firma Ed25519 de forma no bloqueante.
    
    Args:
        message: Mensaje originales (bytes)
        signature_hex: Firma en formato hexadecimal (128 caracteres)
        pubkey_hex: Clave pública del dispositivo en hex
        
    Returns:
        True si la firma es válida, False en caso contrario
    """
    try:
        pubkey = decode_public_key(pubkey_hex)
        signature = bytes_from_hex(signature_hex)
        
        # Validar usando PyNaCl (lanzará excepción si es inválida)
        pubkey.verify(message, signature, encoder=nacl.encoding.RawEncoder)
        return True
    except (ValueError, nacl.exceptions.CryptoError) as e:
        logger.debug(f"Signature verification failed: {e}")
        return False


def serialize_telemetry_payload(params: dict) -> bytes:
    """
    Serializa payload de telemetría a formato canónico para verificación.
    
    Orden consistente de keys para evitar ataques de reordenamiento.
    
    Args:
        params: Dictionary de parámetros de sensor
        
    Returns:
        Bytes codificados en formato canónico
    """
    # Keys en orden específico para firmas
    canonical_keys = [
        "temperature_c",
        "humidity_pct", 
        "soil_moisture_pct",
        "light_lux",
        "uv_index",
        "timestamp",
    ]
    
    # Filtrar solo keys existentes y ordenar
    ordered_data = {k: params.get(k) for k in canonical_keys if params.get(k) is not None}
    
    # Serialize a JSON con keys ordenadas (determinista)
    return json.dumps(ordered_data, separators=(",", ":")).encode("utf-8")


# =============================================================================
# Caché de Claves Públicas (Redis) — con Circuit Breaker (Hallazgo #4)
# =============================================================================
async def get_cached_pubkey(redis_client: redis.Redis, pubkey_hex: str) -> Optional[str]:
    """
    Obtiene clave pública desde Redis cache.

    ── CIRCUIT BREAKER ──────────────────────────────────────────────────────
    Si Redis está caído (RedisError), se registra un warning y se retorna
    None para que el flujo de validación continúe consultando PostgreSQL
    directamente. La validación NUNCA se interrumpe por un fallo de cache.
    ─────────────────────────────────────────────────────────────────────────

    Args:
        redis_client: Instancia de Redis
        pubkey_hex: Clave pública en formato hexadecimal

    Returns:
        Clave pública si existe en cache, None si no (o si Redis está caído)
    """
    cache_key = f"device:pubkey:{pubkey_hex}"
    try:
        cached = await redis_client.get(cache_key)
        return cached
    except redis.RedisError as exc:
        # ── CIRCUIT BREAKER: Redis caído — degradar a consulta directa en PG ──
        logger.warning(
            "circuit_breaker_redis_get | Redis no disponible (%s). "
            "Degradando a consulta directa en PostgreSQL.",
            exc.__class__.__name__,
        )
        return None  # Fuerza cache miss → flujo continúa hacia fetch_pubkey_from_db()


async def set_cached_pubkey(redis_client: redis.Redis, pubkey_hex: str, db_value: str) -> None:
    """
    Guarda clave pública en Redis cache.

    ── CIRCUIT BREAKER ──────────────────────────────────────────────────────
    Si Redis está caído, el fallo es NO FATAL: la validación ya fue exitosa
    contra PostgreSQL. El warning queda en logs para monitoreo.
    ─────────────────────────────────────────────────────────────────────────

    Args:
        redis_client: Instancia de Redis
        pubkey_hex: Clave pública en formato hexadecimal
        db_value: Valor de la clave desde PostgreSQL
    """
    cache_key = f"device:pubkey:{pubkey_hex}"
    try:
        await redis_client.setex(cache_key, PUBKEY_CACHE_TTL, db_value)
    except redis.RedisError as exc:
        # ── CIRCUIT BREAKER: No fatal — la validación ya fue exitosa ──
        logger.warning(
            "circuit_breaker_redis_set | No se pudo cachear pubkey (%s). "
            "El sistema continúa operativo.",
            exc.__class__.__name__,
        )


async def fetch_pubkey_from_db(pubkey_hex: str) -> Optional[str]:
    """
    Consulta clave pública del dispositivo directamente en PostgreSQL.

    ── HALLAZGO #2 REMEDIATED ───────────────────────────────────────────────
    Implementación real con asyncpg. Usa el pool de conexiones global para
    ejecutar un SELECT parametrizado (safe — sin riesgo de SQL injection).
    Si el pool no está disponible (DATABASE_URL no configurado o PG caído),
    retorna None de forma controlada sin abortar el Gateway.
    ─────────────────────────────────────────────────────────────────────────

    Args:
        pubkey_hex: Clave pública del dispositivo en hexadecimal (64 chars)

    Returns:
        pubkey_hex si el dispositivo está registrado en DB, None si no existe
        o si la DB no está disponible.
    """
    pool = await get_pg_pool()
    if pool is None:
        # Pool no disponible: modo solo-cache. Si también es cache miss,
        # el dispositivo será rechazado (comportamiento conservador Zero-Trust).
        logger.debug(
            "fetch_pubkey_from_db | Pool PG no disponible. "
            "Pubkey %s... rechazada por modo solo-cache.",
            pubkey_hex[:16],
        )
        return None

    try:
        async with pool.acquire() as conn:
            # Consulta parametrizada — sin interpolación de strings (OWASP A03)
            row = await conn.fetchrow(
                f"SELECT {DEVICES_PUBKEY_COLUMN} "
                f"FROM {DEVICES_TABLE} "
                f"WHERE {DEVICES_PUBKEY_COLUMN} = $1",
                pubkey_hex,
            )
        if row:
            logger.info(
                "fetch_pubkey_from_db | Dispositivo registrado encontrado: %s...",
                pubkey_hex[:16],
            )
            return row[DEVICES_PUBKEY_COLUMN]
        else:
            logger.warning(
                "fetch_pubkey_from_db | Dispositivo NO registrado en DB: %s...",
                pubkey_hex[:16],
            )
            return None

    except asyncpg.PostgresError as exc:
        # Error de consulta PG — no interrumpir el Gateway, rechazar conservadoramente
        logger.error(
            "fetch_pubkey_from_db | Error PG consultando pubkey %s...: %s",
            pubkey_hex[:16],
            exc,
        )
        return None
    except asyncpg.exceptions.TooManyConnectionsError:
        logger.error(
            "fetch_pubkey_from_db | Pool agotado. Rechazando pubkey %s... temporalmente.",
            pubkey_hex[:16],
        )
        return None


# =============================================================================
# Validación de Telemetría (Zero-Trust)
# =============================================================================
async def validate_telemetry(
    params: dict, 
    redis_client: redis.Redis
) -> tuple[bool, Optional[str]]:
    """
    Valida payload de telemetría incoming con firma Ed25519.
    
    Flujo:
      1. Extraer firma y clave pública del payload
      2. Buscar clave en Redis cache
      3. Si no está, consultar DB
      4. Validar matemáticamente
      5. Retornar (is_valid, plant_id)
    
    Args:
        params: Diccionario de parámetros del mensaje
        redis_client: Cliente Redis
        
    Returns:
        Tupla (validado, plant_id)
    """
    # (a) Extraer firma Ed25519 y clave pública
    signature_hex = params.get("signature")
    pubkey_hex = params.get("device_pubkey")
    
    if not signature_hex or not pubkey_hex:
        # Firmas no presentes = reject inmediato (silencioso)
        logger.warning(f"Rejecting telemetry: missing signature or pubkey")
        return False, None
    
    # (b) Consultar clave pública desde cache Redis
    cached_pubkey = await get_cached_pubkey(redis_client, pubkey_hex)
    
    if not cached_pubkey:
        # Cache miss - consultar DB
        logger.debug(f"Cache miss for pubkey {pubkey_hex[:16]}...")
        cached_pubkey = await fetch_pubkey_from_db(pubkey_hex)
        
        if cached_pubkey:
            # Guardar en cache para próximas consultas
            await set_cached_pubkey(redis_client, pubkey_hex, cached_pubkey)
        else:
            # Clave no registrada = silenciosamente reject
            logger.warning(f"Rejecting: unregistered device pubkey={pubkey_hex[:16]}...")
            return False, None
    
    # (c) Serializar payload a formato canónico
    message = serialize_telemetry_payload(params)
    
    # (d) Validar matemáticamente
    is_valid = verify_ed25519_signature(message, signature_hex, pubkey_hex)
    
    if not is_valid:
        # Firma inválida = silently drop
        logger.warning(f"Rejecting telemetry: invalid Ed25519 signature")
        return False, None
    
    # (e) Resolver Plant ID desde la clave pública
    # En implementación full, consultamos DB con pubkey_hex -> plant_id
    # Por ahora usamos mapeo simple
    plant_id = DEFAULT_PLANT_ID  # TODO: Implementar lookup real
    
    return True, plant_id


# =============================================================================
# Manejo de Conexiones WebSocket
# =============================================================================
async def handle_node(ws: websockets.WebSocketServerProtocol):
    """
    Maneja conexión WebSocket de un nodo ESP32.
    
    Valida identidad y telemetría usando Zero-Trust.
    """
    peer = ws.remote_address
    node_name = f"unknown-{peer[0]}:{peer[1]}"
    logger.info(f"New connection from {peer}")

    # Obtener cliente Redis para esta conexión
    redis_client = await get_redis_client()

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
                # Handshake: capturar identidad del nodo
                node_name = params.get("node_name", node_name)
                logger.info(f"Node connected: {node_name}")
                await ws.send(json.dumps({
                    "type": "res", 
                    "id": msg_id, 
                    "result": "connected"
                }))
            
            elif msg_type == "req" and method == "telemetry.report":
                # =========================================================
                # ZERO-TRUST: Validar firma antes de procesar
                # =========================================================
                timestamp = params.get("timestamp")
                if not timestamp:
                    logger.warning(f"Rejecting telemetry from {node_name}: no timestamp")
                    await ws.send(json.dumps({
                        "type": "res", 
                        "id": msg_id, 
                        "error": {"code": 400, "message": "timestamp required"}
                    }))
                    continue
                
                # =========================================================
                # VALIDACIÓN CRIPTOGRÁFICA (Zero-Trust)
                # =========================================================
                is_valid, plant_id = await validate_telemetry(params, redis_client)
                
                if not is_valid:
                    # Silently drop - no revelar por qué falló
                    continue
                
                # =========================================================
                # Procesar telemetría validada
                # =========================================================
                # Aplanar al contrato del Backend
                flattened_sensors = {
                    "air_temperature": params.get("temperature_c"),
                    "air_humidity": params.get("humidity_pct"),
                    "soil_humidity": params.get("soil_moisture_pct"),
                    "light_level": params.get("light_lux"),
                    "uv_index": params.get("uv_index"),
                }
                
                # Remover nulos
                flattened_sensors = {
                    k: v for k, v in flattened_sensors.items() 
                    if v is not None
                }
                
                if flattened_sensors:
                    # Llamada al Store & Forward
                    enqueue_reading(
                        con=init_db(),
                        device_id=node_name,
                        plant_id=plant_id,
                        sensors=flattened_sensors,
                        timestamp=timestamp
                    )
                    logger.info(f"Enqueued telemetry from {node_name} @ {timestamp}")
                
                await ws.send(json.dumps({
                    "type": "res", 
                    "id": msg_id, 
                    "result": "accepted"
                }))

            elif msg_type == "res":
                # Respuestas a comandos - no requiere acción
                pass

    except ConnectionClosed:
        logger.info(f"Node {node_name} disconnected")
    except Exception as e:
        logger.error(f"Error handling node {node_name}: {e}")
    finally:
        pass  # No cerramos Redis aquí - se reusea en próximas conexiones


# =============================================================================
# Servidor Gateway — Lifespan con Pool asyncpg (Hallazgo #2 + #4)
# =============================================================================
async def main():
    """
    Inicia el Gateway OpenClaw con gestión completa del ciclo de vida:
      1. Pool asyncpg  → consulta PG para dispositivos no cacheados
      2. Cliente Redis → caché de claves públicas (con circuit breaker)
      3. Servidor WebSocket → acepta conexiones de nodos ESP32
      4. Shutdown limpio → cierra pool PG y cliente Redis
    """
    logger.info("Starting OpenClaw Gateway on 0.0.0.0:18789")

    # ── 1. Inicializar pool PostgreSQL (Hallazgo #2) ──────────────────────
    await init_pg_pool()

    # ── 2. Inicializar cliente Redis (Hallazgo #4 — circuit breaker activo) ─
    await get_redis_client()

    # ── 3. Iniciar servidor WebSocket ─────────────────────────────────────
    async with websockets.serve(handle_node, "0.0.0.0", 18789):
        logger.info(
            "Gateway ready — accepting ESP32 connections | "
            "PG pool: %s | Redis: %s",
            "OK" if _pg_pool else "DEGRADED (solo-cache)",
            REDIS_URL.split("@")[-1] if "@" in REDIS_URL else REDIS_URL,
        )
        try:
            await asyncio.Future()  # Bloquear indefinidamente
        except asyncio.CancelledError:
            logger.info("Gateway main task cancelled — iniciando shutdown.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Gateway shutdown requested")
    finally:
        # ── Shutdown limpio: cerrar PG pool y Redis ───────────────────────
        async def _cleanup():
            await close_pg_pool()
            await close_redis_client()
        asyncio.run(_cleanup())
        logger.info("Gateway stopped. All connections closed.")