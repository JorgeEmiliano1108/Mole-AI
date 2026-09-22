/*
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * fee2_frame.c — Fixed-point LE encoder for BLE FEE2 live telemetry.
 *
 * Implements gatt-fee2-spec.md §2. Pure C: compiles for ESP-IDF and host gcc.
 */
#include <math.h>
#include <stdlib.h>
#include "fee2_frame.h"
#include "mole_config.h"

static void put_u16le(uint8_t *p, uint16_t v) {
    p[0] = (uint8_t)(v & 0xFF);
    p[1] = (uint8_t)((v >> 8) & 0xFF);
}

static void put_u32le(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)(v & 0xFF);
    p[1] = (uint8_t)((v >> 8) & 0xFF);
    p[2] = (uint8_t)((v >> 16) & 0xFF);
    p[3] = (uint8_t)((v >> 24) & 0xFF);
}

static int clamp_i(int v, int lo, int hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

int fee2_encode(const edge_frame_t *frame, uint8_t *out, size_t out_size) {
    if (!frame || !out) return -1;

    int valid = frame->ambient_valid & 0x0F;

    int ri = frame->report_interval_minutes;
    if (ri < 1) ri = MOLE_REPORT_INTERVAL_DEFAULT;
    if (ri > 120) ri = 120;

    int soil_count = frame->soil_count;
    if (soil_count < 0) soil_count = 0;
    if (soil_count > EDGE_FRAME_MAX_SOIL_PINS) {
        soil_count = EDGE_FRAME_MAX_SOIL_PINS;
    }

    /* ── Worst case: count every requested probe (invalid pins skipped later,
     * so the real length can only be ≤ this bound) ─────────────────────── */
    int need = 4 + 1 + 1;
    if (valid & AMBIENT_VALID_TEMP_BIT)  need += 2;
    if (valid & AMBIENT_VALID_HUM_BIT)   need += 2;
    if (valid & AMBIENT_VALID_LIGHT_BIT) need += 2;
    if (valid & AMBIENT_VALID_UV_BIT)    need += 2;
    need += 1 + 2 * soil_count;
    if (out_size < (size_t)need) return -1;

    size_t o = 0;
    put_u32le(&out[o], (uint32_t)frame->ts); o += 4;
    out[o++] = (uint8_t)ri;
    out[o++] = (uint8_t)valid;

    if (valid & AMBIENT_VALID_TEMP_BIT) {
        int q = clamp_i((int)lroundf(frame->ambient.t * 100.0f), -32768, 32767);
        put_u16le(&out[o], (uint16_t)(int16_t)q); o += 2;
    }
    if (valid & AMBIENT_VALID_HUM_BIT) {
        int q = clamp_i((int)lroundf(frame->ambient.h * 100.0f), 0, 65535);
        put_u16le(&out[o], (uint16_t)q); o += 2;
    }
    if (valid & AMBIENT_VALID_LIGHT_BIT) {
        int q = clamp_i((int)lroundf(frame->ambient.l), 0, 65535);
        put_u16le(&out[o], (uint16_t)q); o += 2;
    }
    if (valid & AMBIENT_VALID_UV_BIT) {
        int q = clamp_i((int)lroundf(frame->ambient.u * 100.0f), 0, 65535);
        put_u16le(&out[o], (uint16_t)q); o += 2;
    }

    /* Soil count is patched after skipping invalid pins. */
    size_t count_pos = o;
    out[o++] = 0;
    int written = 0;
    for (int i = 0; i < soil_count; i++) {
        const char *pin = frame->soil[i].pin;
        int gpio = pin ? atoi(pin) : -1;
        int ch = MOLE_GPIO_TO_ADC1_CHANNEL(gpio);
        if (ch < 0 || ch > 7) continue;  /* non-ADC1 pin: skip, never fatal */
        int adc = clamp_i(frame->soil[i].adc_raw, ADC_RAW_MIN, ADC_RAW_MAX);
        out[o++] = (uint8_t)(((ch & 0x07) << 4) | ((adc >> 8) & 0x0F));
        out[o++] = (uint8_t)(adc & 0xFF);
        written++;
    }
    out[count_pos] = (uint8_t)written;

    return (int)o;
}
