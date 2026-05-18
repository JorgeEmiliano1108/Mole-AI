/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * mole_config.h — Compile-time constants for the Mole.AI Telemetry Node.
 * =============================================================================
 */
#pragma once

/* Firmware version — embedded in WebSocket connect handshake */
#define MOLE_FW_VERSION       "3.0.0"
#define MOLE_NODE_NAME        "mole-agri-sensor"

/* NVS namespace and keys for provisioning data */
#define MOLE_NVS_NAMESPACE    "mole_prov"
#define MOLE_NVS_KEY_TOKEN    "auth_token"

/* Deep Sleep fallback (when no WebSocket session is active) */
#define MOLE_DEEP_SLEEP_US     (300ULL * 1000000ULL)  /* 5 minutes */

/* Sensor I2C addresses */
#define MOLE_DHT20_ADDR        0x38
#define MOLE_LTR390_ADDR       0x53

/* ── ADC1 Soil Sensor Pin Configuration ─────────────────────────────────── */
/* RESTRICCIÓN HARDWARE: Solo pines ADC1 (32-39) son seguros con WiFi activo.
 * ADC2 (GPIO 0,2,4,12-15,25-27) entra en conflicto con la radio WiFi.
 * Cada pin corresponde a un sensor de humedad clavado en una planta distinta.
 * El número de pin se usa como llave en el JSON: "soil": {"32": 45.1, ...}
 */
#define MOLE_ACTIVE_SOIL_PINS      {32, 33}
#define MOLE_NUM_ACTIVE_SOIL_PINS  2

/* GPIO-to-ADC1-Channel mapping (ESP32 specific) */
#define MOLE_GPIO_TO_ADC1_CHANNEL(gpio) ( \
    (gpio) == 36 ? 0 : \
    (gpio) == 37 ? 1 : \
    (gpio) == 38 ? 2 : \
    (gpio) == 39 ? 3 : \
    (gpio) == 32 ? 4 : \
    (gpio) == 33 ? 5 : \
    (gpio) == 34 ? 6 : \
    (gpio) == 35 ? 7 : -1 )

/* ADC calibration defaults for capacitive soil sensor */
#define MOLE_SOIL_AIR_VAL      4095
#define MOLE_SOIL_WATER_VAL    1500

/* Captive Portal AP configuration */
#define MOLE_AP_SSID           "MoleAI-Setup"
#define MOLE_AP_PASS           "mole1234"
#define MOLE_AP_MAX_CONN       2
#define MOLE_AP_CHANNEL        0
