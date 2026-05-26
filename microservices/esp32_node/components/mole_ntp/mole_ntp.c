/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * mole_ntp.c — SNTP synchronization for Anti-Replay compliance
 *
 * ETSI EN 303 645 §5.6: Devices SHALL use secure, reliable time sources.
 * Three redundant NTP servers: pool.ntp.org, time.google.com, time.cloudflare.com
 * =============================================================================
 */

#include <string.h>
#include <time.h>
#include <sys/time.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_sntp.h"
#include "mole_ntp.h"

static const char *TAG = "MOLE_NTP";
static volatile bool s_synced = false;

/* ── Callback from SNTP stack ────────────────────────────────────────────── */
static void ntp_sync_notification(struct timeval *tv)
{
    ESP_LOGI(TAG, "NTP time synchronized");
    s_synced = true;
}

esp_err_t mole_ntp_init(void)
{
    ESP_LOGI(TAG, "Initializing SNTP (triple-redundant)...");

    esp_sntp_setoperatingmode(SNTP_OPMODE_POLL);
    esp_sntp_setservername(0, CONFIG_MOLE_NTP_SERVER_PRIMARY);
    esp_sntp_setservername(1, CONFIG_MOLE_NTP_SERVER_SECONDARY);
    esp_sntp_setservername(2, CONFIG_MOLE_NTP_SERVER_TERTIARY);
    sntp_set_time_sync_notification_cb(ntp_sync_notification);

    esp_sntp_init();

    /* Force UTC timezone — no DST offset */
    setenv("TZ", "UTC0", 1);
    tzset();

    return ESP_OK;
}

esp_err_t mole_ntp_wait_sync(uint32_t timeout_ms)
{
    ESP_LOGI(TAG, "Waiting for NTP sync (timeout=%lums)...", (unsigned long)timeout_ms);

    uint32_t elapsed = 0;
    const uint32_t step = 500;

    while (!s_synced && elapsed < timeout_ms) {
        vTaskDelay(pdMS_TO_TICKS(step));
        elapsed += step;
    }

    if (s_synced) {
        char ts[32];
        mole_ntp_get_iso8601(ts, sizeof(ts));
        ESP_LOGI(TAG, "Clock synced: %s", ts);
        return ESP_OK;
    }

    ESP_LOGW(TAG, "NTP sync timed out after %lums", (unsigned long)timeout_ms);
    return ESP_ERR_TIMEOUT;
}

bool mole_ntp_is_synced(void)
{
    return s_synced;
}

esp_err_t mole_ntp_get_iso8601(char *buf, size_t buf_len)
{
    if (!buf || buf_len < 21) return ESP_ERR_INVALID_ARG;

    time_t now;
    time(&now);
    struct tm timeinfo;
    gmtime_r(&now, &timeinfo);
    strftime(buf, buf_len, "%Y-%m-%dT%H:%M:%SZ", &timeinfo);

    return ESP_OK;
}
