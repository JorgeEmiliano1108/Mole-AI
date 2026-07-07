/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * sensor_ltr390.c — Native ESP-IDF I2C driver for Lite-On LTR-390UV-01
 *
 * Replaces: Arduino Adafruit_LTR390 library (LEGACY/)
 * Registers per datasheet rev 1.1
 * =============================================================================
 */

#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "sensor_ltr390.h"

static const char *TAG = "LTR390";

#define LTR390_ADDR        0x53   /* per datasheet rev 1.1 */

/* Register addresses */
#define LTR390_REG_CTRL     0x00  /* Main control */
#define LTR390_REG_MEAS     0x04  /* Meas rate / resolution */
#define LTR390_REG_GAIN     0x05  /* Gain */
#define LTR390_REG_PART_ID  0x06  /* Part ID (should read 0xB2) */
#define LTR390_REG_STATUS   0x07  /* Status (bit 3 = data ready) */
#define LTR390_REG_ALS_L    0x0D  /* ALS data low byte */
#define LTR390_REG_ALS_M    0x0E  /* ALS data mid byte */
#define LTR390_REG_ALS_H    0x0F  /* ALS data high byte */
#define LTR390_REG_UVS_L    0x10  /* UVS data low byte */
#define LTR390_REG_UVS_M    0x11  /* UVS data mid byte */
#define LTR390_REG_UVS_H    0x12  /* UVS data high byte */

/* Mode bits for CTRL register */
#define LTR390_MODE_ALS     0x02  /* Enable ALS, sensor active */
#define LTR390_MODE_UVS     0x0A  /* Enable UVS, sensor active */

/* Gain = 3x, Resolution = 16-bit (meas rate register) */
#define LTR390_GAIN_3X      0x01
#define LTR390_RES_16BIT    0x20  /* 16-bit, 25ms integration */

/* Conversion factors for gain=3x, 16-bit resolution (per datasheet AN-001) */
/* lux = raw_als * ALS_LUX_FACTOR */
#define ALS_LUX_FACTOR      0.06f
/* UV Index = raw_uvs * UVS_UVI_FACTOR */
#define UVS_UVI_FACTOR      0.23f

#define LTR390_STATUS_READY 0x08

struct sensor_ltr390 {
    i2c_master_dev_handle_t dev;
};

static esp_err_t write_reg(i2c_master_dev_handle_t dev,
                           uint8_t reg, uint8_t val)
{
    uint8_t buf[2] = {reg, val};
    return i2c_master_transmit(dev, buf, 2, 100);
}

static esp_err_t read_reg(i2c_master_dev_handle_t dev,
                          uint8_t reg, uint8_t *out, size_t len)
{
    return i2c_master_transmit_receive(dev, &reg, 1, out, len, 100);
}

static uint32_t read_20bit(i2c_master_dev_handle_t dev, uint8_t reg_low)
{
    uint8_t buf[3] = {0};
    read_reg(dev, reg_low, buf, 3);
    return (uint32_t)buf[0] | ((uint32_t)buf[1] << 8) |
           (((uint32_t)buf[2] & 0x0F) << 16);
}

esp_err_t sensor_ltr390_init(i2c_master_bus_handle_t bus,
                             sensor_ltr390_handle_t *out_handle)
{
    struct sensor_ltr390 *s = calloc(1, sizeof(*s));
    if (!s) return ESP_ERR_NO_MEM;

    i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address  = LTR390_ADDR,
        .scl_speed_hz    = 100000,
    };
    esp_err_t err = i2c_master_bus_add_device(bus, &cfg, &s->dev);
    if (err != ESP_OK) { free(s); return err; }

    /* Verify part ID */
    uint8_t part_id = 0;
    read_reg(s->dev, LTR390_REG_PART_ID, &part_id, 1);
    if ((part_id >> 4) != 0x0B) {
        ESP_LOGE(TAG, "Part ID mismatch: 0x%02X (expected 0xBx)", part_id);
        free(s);
        return ESP_ERR_NOT_FOUND;
    }

    /* Configure gain and resolution */
    write_reg(s->dev, LTR390_REG_GAIN, LTR390_GAIN_3X);
    write_reg(s->dev, LTR390_REG_MEAS, LTR390_RES_16BIT);

    ESP_LOGI(TAG, "LTR390 initialized at 0x%02X (gain=3x, 16-bit)",
             LTR390_ADDR);
    *out_handle = s;
    return ESP_OK;
}

esp_err_t sensor_ltr390_read(sensor_ltr390_handle_t handle,
                             float *lux, float *uv_index)
{
    if (!handle || !lux || !uv_index) return ESP_ERR_INVALID_ARG;

    /* ── ALS mode ──────────────────────────────────────────────────── */
    write_reg(handle->dev, LTR390_REG_CTRL, LTR390_MODE_ALS);
    vTaskDelay(pdMS_TO_TICKS(100));

    uint8_t status = 0;
    read_reg(handle->dev, LTR390_REG_STATUS, &status, 1);
    uint32_t raw_als = read_20bit(handle->dev, LTR390_REG_ALS_L);
    *lux = (status & LTR390_STATUS_READY) ? (float)raw_als * ALS_LUX_FACTOR : -1.0f;

    /* ── UVS mode ──────────────────────────────────────────────────── */
    write_reg(handle->dev, LTR390_REG_CTRL, LTR390_MODE_UVS);
    vTaskDelay(pdMS_TO_TICKS(100));

    read_reg(handle->dev, LTR390_REG_STATUS, &status, 1);
    uint32_t raw_uvs = read_20bit(handle->dev, LTR390_REG_UVS_L);
    *uv_index = (status & LTR390_STATUS_READY) ? (float)raw_uvs * UVS_UVI_FACTOR : -1.0f;

    ESP_LOGD(TAG, "lux=%.1f uv=%.2f (raw_als=%lu raw_uvs=%lu)",
             *lux, *uv_index, raw_als, raw_uvs);
    return ESP_OK;
}
