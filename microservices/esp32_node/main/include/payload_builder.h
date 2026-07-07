/*
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * payload_builder.h — Builds compact edge-batch JSON from edge_frame_t
 *
 * Output: {"ts":...,"ri":...,"a":{"t":...,"h":...,"l":...,"u":...},
 *          "s":[{"p":"32","v":2847},...],"dg":0}
 */
#pragma once

#include <stddef.h>
#include "edge_frame.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Build a compact edge-batch JSON payload from a telemetry frame.
 *
 * Uses cJSON_PrintPreallocated with a static buffer of PAYLOAD_BUFFER_SIZE.
 * No heap allocation after initial cJSON object creation.
 *
 * @param frame    Valid edge_frame_t with ts, sensors, ambient_valid bitmask
 * @param out      Output buffer (must be >= PAYLOAD_BUFFER_SIZE)
 * @param out_size Size of output buffer
 * @return Number of bytes written (excluding null terminator), or -1 on error
 */
int payload_build(const edge_frame_t *frame, char *out, size_t out_size);

#define PAYLOAD_BUFFER_SIZE   512  /* enough for max payload (~180 bytes + overhead) */

#ifdef __cplusplus
}
#endif
