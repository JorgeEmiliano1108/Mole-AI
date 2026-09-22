/*
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * fee2_frame.h — Fixed-point LE encoder for BLE FEE2 live telemetry.
 *
 * Mirror of edge_frame_t (edge_frame.h) in the wire format defined by
 * microservices/esp32_node/docs/gatt-fee2-spec.md §2:
 *   ts:u32 | ri:u8 | valid:u8 | t?:i16 | h?:u16 | l?:u16 | u?:u16
 *   | soil_count:u8 | N×{2B: ch(3b)+adc(12b)}
 * Ambient ×100 (°C, %, UVI); lux raw u16. Soil: ADC1 channel + 12-bit ADC.
 */
#pragma once

#include <stddef.h>
#include <stdint.h>
#include "edge_frame.h"

#ifdef __cplusplus
extern "C" {
#endif

/** Maximum encoded frame: 6 + 8 + 1 + 8×2 = 31 bytes. */
#define FEE2_MAX_FRAME_LEN   32

/**
 * @brief Encode a telemetry frame to the FEE2 fixed-point wire format.
 *
 * Pure C (no ESP-IDF deps) — host-testable. Never exposes auth tokens
 * or PII: only ts/ri/sensor quantities (enforce-compliance LFPDPPP).
 *
 * @param frame    Valid edge_frame_t (ambient floats, soil pin strings)
 * @param out      Output buffer (≥ FEE2_MAX_FRAME_LEN recommended)
 * @param out_size Size of output buffer
 * @return Bytes written (11..31), or -1 on NULL args / short buffer.
 *         Entries with invalid GPIO pins are skipped, never fatal.
 */
int fee2_encode(const edge_frame_t *frame, uint8_t *out, size_t out_size);

#ifdef __cplusplus
}
#endif
