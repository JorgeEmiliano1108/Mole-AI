/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * mole_config.h — Compile-time constants for the Mole.AI OpenClaw node.
 *
 * IFT-016:       Default TX power only. No EIRP overrides in this firmware.
 * ETSI EN 303645: NTP required before any telemetry emission.
 * LFPDPPP:       Zero PII in flash. Device identity = Ed25519 pubkey.
 * =============================================================================
 */
#pragma once

/* Firmware version — embedded in OpenClaw connect handshake */
#define MOLE_FW_VERSION       "2.1.0"
#define MOLE_NODE_ROLE        "node"
#define MOLE_NODE_NAME        "mole-agri-sensor"

/* NVS namespace for identity storage */
#define MOLE_NVS_NAMESPACE    "mole_id"
#define MOLE_NVS_KEY_PRIV     "ed25519_priv"
#define MOLE_NVS_KEY_PUB      "ed25519_pub"

/* Ed25519 key sizes */
#define MOLE_ED25519_PRIV_LEN  64
#define MOLE_ED25519_PUB_LEN   32
#define MOLE_ED25519_SIG_LEN   64

/* Deep Sleep fallback (when no WebSocket session is active) */
#define MOLE_DEEP_SLEEP_US     (300ULL * 1000000ULL)  /* 5 minutes */

/* Sensor I2C addresses */
#define MOLE_DHT20_ADDR        0x38
#define MOLE_LTR390_ADDR       0x53

/* ADC calibration defaults for capacitive soil sensor */
#define MOLE_SOIL_AIR_VAL      4095
#define MOLE_SOIL_WATER_VAL    1500
