#!/usr/bin/env python3
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
Mock IoT Client Simulator - Mole AI
====================================
Simula un dispositivo IoT (ESP32/Raspberry Pi) enviando telemetría de sensores
a intervalos regulares. Los datos incluyen:
  - ID de planta ficticio
  - Sensores: pH, humedad, temperatura, luz UV
  - Fotografía simulada en Base64 (formato JPG mínimo)

Autenticación:
  - Usa API Key desde archivo .env (HARDWARE_API_KEY)
  - Envía la clave en header: X-Hardware-Api-Key

Endpoints:
  - POST http://127.0.0.1:8000/api/v1/sensor-data/ (Django / ingesta de sensores)

Ejecución:
  python mock_iot_client.py
"""

import json
import time
import requests
import base64
import logging
import os
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN DEL CLIENTE IoT MOCK
# ============================================================================

# Endpoint Django para registrar datos de sensores
SENSOR_DATA_ENDPOINT = "http://127.0.0.1:8000/api/v1/sensor-data/"

# Intervalo de envío (en segundos)
SEND_INTERVAL = 5

# ID de planta ficticio (simula un dispositivo específico)
PLANT_ID = "plant_001_manzanilla"

# Leer API Key desde .env (requerida para autenticación M2M)
HARDWARE_API_KEY = os.getenv('HARDWARE_API_KEY')
if not HARDWARE_API_KEY:
    logger.error("HARDWARE_API_KEY not set. Exiting to avoid insecure default usage.")
    raise SystemExit("HARDWARE_API_KEY not set. Set it in your environment or .env (do NOT commit .env).")

# ============================================================================
# DATOS ESTÁTICOS DE SENSORES — Wide Table (columnas directas)
# ============================================================================

SENSOR_VALUES = {
    "soil_humidity":    65.0,   # % humedad del suelo
    "air_temperature":  25.3,   # °C temperatura ambiental
    "uv_index":         5.2,    # índice UV
    "light_level":      450.0,  # lux intensidad de luz
    "ph_level":         6.5,    # pH del suelo
}

# ============================================================================
# IMAGEN SIMULADA (Mínima foto JPG válida en Base64)
# ============================================================================
# Esta es una imagen JPG de 1x1 píxel de color rojo (tamaño mínimo válido)
FAKE_PHOTO_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def generate_sensor_payload() -> Dict[str, Any]:
    """
    Genera el payload JSON que se enviará al servidor.
    Formato Wide-Table: campos planos de sensores + foto simulada.
    """
    payload = {
        "plant_id": PLANT_ID,
        "recorded_at": datetime.now().isoformat(),
        # Columnas de sensores (Wide Table)
        **SENSOR_VALUES,
        # Foto simulada (OV2640 captura)
        "image_base64": FAKE_PHOTO_BASE64,
    }
    
    return payload

def send_sensor_data(payload: Dict[str, Any]) -> bool:
    """
    Envía el payload JSON al servidor con autenticación por API Key.
    
    Args:
        payload: Diccionario con los datos del sensor.
    
    Returns:
        True si el envío fue exitoso, False en caso contrario.
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "X-Hardware-Api-Key": HARDWARE_API_KEY,  # Autenticación M2M
        }
        
        logger.info(f"📡 Enviando datos a {SENSOR_DATA_ENDPOINT}...")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            SENSOR_DATA_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Datos enviados exitosamente (Status: {response.status_code})")
            logger.debug(f"Respuesta: {response.text}")
            return True
        else:
            logger.warning(f"⚠️ Status inesperado: {response.status_code}")
            logger.debug(f"Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Error de conexión: {e}")
        logger.info(f"💡 Asegúrate de que Django esté ejecutándose en {SENSOR_DATA_ENDPOINT}")
        return False
    except requests.exceptions.Timeout as e:
        logger.error(f"❌ Timeout en la solicitud: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return False

def main():
    """
    Bucle principal del simulador IoT.
    Envía datos de sensores cada SEND_INTERVAL segundos.
    """
    logger.info("=" * 70)
    logger.info("🚀 INICIANDO SIMULADOR IoT - Mole AI")
    logger.info("=" * 70)
    logger.info(f"📍 Endpoint de destino: {SENSOR_DATA_ENDPOINT}")
    logger.info(f"🔑 API Key: {HARDWARE_API_KEY[:20]}..." if len(HARDWARE_API_KEY) > 20 else f"🔑 API Key: {HARDWARE_API_KEY}")
    logger.info(f"⏱️  Intervalo de envío: {SEND_INTERVAL} segundos")
    logger.info(f"🌱 ID de planta: {PLANT_ID}")
    logger.info("=" * 70)
    logger.info("Presiona Ctrl+C para detener el simulador.")
    logger.info("=" * 70)
    logger.info("")
    
    try:
        iteration = 0
        while True:
            iteration += 1
            
            logger.info(f"--- ITERACIÓN {iteration} ---")
            
            # Generar payload
            payload = generate_sensor_payload()
            
            # Enviar datos
            success = send_sensor_data(payload)
            
            if success:
                logger.info(f"⏰ Próximo envío en {SEND_INTERVAL} segundos...\n")
            else:
                logger.warning(f"⏰ Reintentando en {SEND_INTERVAL} segundos...\n")
            
            # Esperar antes del próximo envío
            time.sleep(SEND_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 70)
        logger.info("⛔ Simulador IoT detenido por el usuario")
        logger.info(f"📊 Total de iteraciones ejecutadas: {iteration}")
        logger.info("=" * 70)

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    main()

