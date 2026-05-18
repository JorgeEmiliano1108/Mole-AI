/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * sensor_dht20.c — Native ESP-IDF I2C driver for ASAIR DHT20
 *
 * Replaces: Arduino DHT20.h library (LEGACY/)
 * Protocol: Trigger measurement (0xAC 0x33 0x00) → wait 80ms → read 7 bytes
 * =============================================================================
 */

#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "sensor_dht20.h"

static const char *TAG = "DHT20";

#define DHT20_ADDR          0x38
#define DHT20_CMD_TRIGGER   0xAC
#define DHT20_ARG1          0x33
#define DHT20_ARG2          0x00
#define DHT20_MEAS_DELAY_MS 80
#define DHT20_STATUS_BUSY   0x80

struct sensor_dht20 {
    i2c_master_dev_handle_t dev;
};

/* ── CRC-8 (polynomial 0x31, init 0xFF) per DHT20 datasheet ──────────── */
static uint8_t crc8(const uint8_t *data, size_t len)
{
    uint8_t crc = 0xFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (int b = 0; b < 8; b++) {
            crc = (crc & 0x80) ? ((crc << 1) ^ 0x31) : (crc << 1);
        }
    }
    return crc;
}

esp_err_t sensor_dht20_init(i2c_master_bus_handle_t bus,
                            sensor_dht20_handle_t *out_handle)
{
    struct sensor_dht20 *s = calloc(1, sizeof(*s));
    if (!s) return ESP_ERR_NO_MEM;

    i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address  = DHT20_ADDR,
        .scl_speed_hz    = 100000,
    };
    esp_err_t err = i2c_master_bus_add_device(bus, &cfg, &s->dev);
    if (err != ESP_OK) {
        free(s);
        return err;
    }

    /* Wait 100ms after power-on for sensor to stabilize */
    vTaskDelay(pdMS_TO_TICKS(100));

    ESP_LOGI(TAG, "DHT20 initialized at 0x%02X", DHT20_ADDR);
    *out_handle = s;
    return ESP_OK;
}

esp_err_t sensor_dht20_read(sensor_dht20_handle_t handle,
                            float *temperature, float *humidity)
{
    if (!handle || !temperature || !humidity) return ESP_ERR_INVALID_ARG;

    /* Trigger measurement */
    uint8_t cmd[3] = {DHT20_CMD_TRIGGER, DHT20_ARG1, DHT20_ARG2};
    esp_err_t err = i2c_master_transmit(handle->dev, cmd, sizeof(cmd), 100);
    if (err != ESP_OK) return err;

    vTaskDelay(pdMS_TO_TICKS(DHT20_MEAS_DELAY_MS));

    /* Read 7 bytes: status + 5 data + CRC */
    uint8_t buf[7] = {0};
    err = i2c_master_receive(handle->dev, buf, sizeof(buf), 100);
    if (err != ESP_OK) return err;

    /* Check busy bit */
    if (buf[0] & DHT20_STATUS_BUSY) {
        ESP_LOGW(TAG, "Sensor busy — measurement not ready");
        return ESP_ERR_TIMEOUT;
    }

    /* Verify CRC */
    uint8_t expected_crc = crc8(buf, 6);
    if (expected_crc != buf[6]) {
        ESP_LOGW(TAG, "CRC mismatch: expected 0x%02X, got 0x%02X",
                 expected_crc, buf[6]);
        return ESP_ERR_INVALID_CRC;
    }

    /* Parse humidity (20-bit) and temperature (20-bit) from raw bytes */
    uint32_t raw_hum = ((uint32_t)(buf[1]) << 12) |
                       ((uint32_t)(buf[2]) << 4)  |
                       ((uint32_t)(buf[3]) >> 4);

    uint32_t raw_temp = (((uint32_t)(buf[3]) & 0x0F) << 16) |
                        ((uint32_t)(buf[4]) << 8)            |
                        ((uint32_t)(buf[5]));

    *humidity    = ((float)raw_hum  / 1048576.0f) * 100.0f;
    *temperature = ((float)raw_temp / 1048576.0f) * 200.0f - 50.0f;

    ESP_LOGD(TAG, "T=%.1f°C  H=%.1f%%", *temperature, *humidity);
    return ESP_OK;
}
