/*
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * edge_frame.h — Compact telemetry frame contract for ESP32 → core_backend
 *
 * Format: {"ts":...,"ri":...,"a":{"t":...,"h":...,"l":...,"u":...},
 *          "s":[{"p":"32","v":2847},...],"dg":0}
 * Contract: POST /api/v1/sensor-data/edge-batch/
 */
#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ── Maximum number of soil sensors ───────────────────────────────────────── */
#define EDGE_FRAME_MAX_SOIL_PINS   8

/* ── Ambient sensor bitmask positions (ambient_valid) ────────────────────── */
#define AMBIENT_VALID_TEMP_BIT     (1 << 0)
#define AMBIENT_VALID_HUM_BIT      (1 << 1)
#define AMBIENT_VALID_LIGHT_BIT    (1 << 2)
#define AMBIENT_VALID_UV_BIT       (1 << 3)

/* ── Degraded bitmask: dg = ~ambient_valid & 0x0F ────────────────────────── */
#define DEGRADED_NONE       0
#define DEGRADED_TEMP_BIT   AMBIENT_VALID_TEMP_BIT
#define DEGRADED_HUM_BIT    AMBIENT_VALID_HUM_BIT
#define DEGRADED_LIGHT_BIT  AMBIENT_VALID_LIGHT_BIT
#define DEGRADED_UV_BIT     AMBIENT_VALID_UV_BIT

/* ── Sensor valid ranges ─────────────────────────────────────────────────── */
#define TEMP_MIN            (-40.0f)
#define TEMP_MAX            80.0f
#define HUM_MIN             0.0f
#define HUM_MAX             100.0f
#define LIGHT_MIN           0.0f
#define LIGHT_MAX           65535.0f
#define UV_MIN              0.0f
#define UV_MAX              15.0f
#define ADC_RAW_MIN         0
#define ADC_RAW_MAX         4095

/* ── Edge frame data structure ────────────────────────────────────────────── */
typedef struct {
    double  ts;                         /* Unix epoch seconds */
    int     report_interval_minutes;    /* 1-120 */

    /* Ambient readings — bitmask en ambient_valid indica campos presentes */
    struct {
        float t;                        /* air_temperature  (°C) */
        float h;                        /* air_humidity     (%)  */
        float l;                        /* light_level      (lux) */
        float u;                        /* uv_index */
    } ambient;
    int ambient_valid;                  /* bit 0=t, 1=h, 2=l, 3=u */

    /* Degraded flag: dg = ~ambient_valid & 0x0F */
    /* Enviado en payload, ignorado por core_backend (DRF unknown fields) */
    /* Guardado en NVS para diagnóstico local */

    /* Soil readings — raw ADC values mapped to hardware pins */
    struct {
        const char *pin;                /* ej: "32", "33" */
        int         adc_raw;            /* 0-4095 */
    } soil[EDGE_FRAME_MAX_SOIL_PINS];
    char soil_pin_storage[EDGE_FRAME_MAX_SOIL_PINS][8];  /* backing store for soil[].pin */
    int soil_count;
} edge_frame_t;

#ifdef __cplusplus
}
#endif
