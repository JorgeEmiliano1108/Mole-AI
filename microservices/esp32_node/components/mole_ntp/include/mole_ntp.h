/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * mole_ntp.h — SNTP time synchronization (ETSI EN 303 645 Anti-Replay)
 *
 * Telemetry MUST NOT be emitted until NTP has synced at least once.
 * =============================================================================
 */
#pragma once

#include "esp_err.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialize SNTP client with triple-redundant NTP servers.
 */
esp_err_t mole_ntp_init(void);

/**
 * @brief Block until NTP synchronization completes or timeout expires.
 * @param timeout_ms  Maximum time to wait in milliseconds
 * @return ESP_OK if synced, ESP_ERR_TIMEOUT if not synced within timeout
 */
esp_err_t mole_ntp_wait_sync(uint32_t timeout_ms);

/**
 * @brief Check if the system clock has been synchronized via NTP.
 */
bool mole_ntp_is_synced(void);

/**
 * @brief Get current UTC time as ISO 8601 string.
 *
 * Format: "2026-04-23T12:00:00Z" (always UTC, no timezone offset)
 * @param buf     Output buffer (minimum 21 bytes)
 * @param buf_len Size of output buffer
 */
esp_err_t mole_ntp_get_iso8601(char *buf, size_t buf_len);

#ifdef __cplusplus
}
#endif
