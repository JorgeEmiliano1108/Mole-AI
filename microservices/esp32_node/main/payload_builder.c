/*
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * payload_builder.c — Builds compact edge-batch JSON from edge_frame_t
 *
 * Dependencies: cJSON (managed_component), edge_frame.h
 * Compiled with: REQUIRES cjson in CMakeLists.txt
 */
#include <string.h>
#include "cJSON.h"
#include "mole_config.h"
#include "payload_builder.h"

int payload_build(const edge_frame_t *frame, char *out, size_t out_size) {
    if (!frame || !out || out_size < 64) return -1;

    cJSON *root = cJSON_CreateObject();
    if (!root) return -1;

    /* ── ts (epoch seconds) ──────────────────────────────────────────── */
    cJSON_AddNumberToObject(root, "ts", frame->ts);

    /* ── ri (report interval, minutes) ───────────────────────────────── */
    int ri = frame->report_interval_minutes;
    if (ri < 1) ri = MOLE_REPORT_INTERVAL_DEFAULT;
    if (ri > 120) ri = 120;
    cJSON_AddNumberToObject(root, "ri", ri);

    /* ── a (ambient readings) ────────────────────────────────────────── */
    int has_ambient = (frame->ambient_valid & 0x0F) != 0;
    if (has_ambient) {
        cJSON *a = cJSON_AddObjectToObject(root, "a");
        if (frame->ambient_valid & AMBIENT_VALID_TEMP_BIT) {
            cJSON_AddNumberToObject(a, "t", frame->ambient.t);
        }
        if (frame->ambient_valid & AMBIENT_VALID_HUM_BIT) {
            cJSON_AddNumberToObject(a, "h", frame->ambient.h);
        }
        if (frame->ambient_valid & AMBIENT_VALID_LIGHT_BIT) {
            cJSON_AddNumberToObject(a, "l", frame->ambient.l);
        }
        if (frame->ambient_valid & AMBIENT_VALID_UV_BIT) {
            cJSON_AddNumberToObject(a, "u", frame->ambient.u);
        }
    }

    /* ── s (soil readings array) ─────────────────────────────────────── */
    int soil_count = frame->soil_count;
    if (soil_count > EDGE_FRAME_MAX_SOIL_PINS) {
        soil_count = EDGE_FRAME_MAX_SOIL_PINS;
    }
    if (soil_count > 0) {
        cJSON *s = cJSON_AddArrayToObject(root, "s");
        for (int i = 0; i < soil_count; i++) {
            cJSON *item = cJSON_CreateObject();
            cJSON_AddStringToObject(item, "p", frame->soil[i].pin ? frame->soil[i].pin : "?");
            cJSON_AddNumberToObject(item, "v", frame->soil[i].adc_raw);
            cJSON_AddItemToArray(s, item);
        }
    }

    /* ── dg (degraded bitmask: ~ambient_valid & 0x0F) ────────────────── */
    int dg = (~frame->ambient_valid) & 0x0F;
    cJSON_AddNumberToObject(root, "dg", dg);

    /* ── Serialize to pre-allocated buffer (no heap alloc after this) ─── */
    int printed = cJSON_PrintPreallocated(root, out, (int)out_size, 0);
    cJSON_Delete(root);

    if (!printed) return -1;
    int len = (int)strlen(out);
    return len;
}
