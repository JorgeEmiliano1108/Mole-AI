/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * sensor_soil.c — ESP-IDF ADC oneshot driver for capacitive soil sensor
 *
 * Replaces: Arduino AnalogMoisture.h (LEGACY/)
 * Uses esp_adc/adc_oneshot.h (ESP-IDF 5.x new ADC API)
 * =============================================================================
 */

#include "esp_log.h"
#include "esp_adc/adc_oneshot.h"
#include "mole_config.h"
#include "sensor_soil.h"

static const char *TAG = "SOIL";

struct sensor_soil {
    adc_oneshot_unit_handle_t adc_handle;
    adc_channel_t             channel;
};

esp_err_t sensor_soil_init(int adc_channel, sensor_soil_handle_t *out_handle)
{
    struct sensor_soil *s = calloc(1, sizeof(*s));
    if (!s) return ESP_ERR_NO_MEM;

    s->channel = (adc_channel_t)adc_channel;

    /* Initialize ADC1 unit */
    adc_oneshot_unit_init_cfg_t unit_cfg = {
        .unit_id = ADC_UNIT_1,
    };
    esp_err_t err = adc_oneshot_new_unit(&unit_cfg, &s->adc_handle);
    if (err != ESP_OK) { free(s); return err; }

    /* Configure the channel: 12-bit width, 11dB attenuation (0–3.3V range) */
    adc_oneshot_chan_cfg_t chan_cfg = {
        .bitwidth = ADC_BITWIDTH_12,
        .atten    = ADC_ATTEN_DB_12,
    };
    err = adc_oneshot_config_channel(s->adc_handle, s->channel, &chan_cfg);
    if (err != ESP_OK) {
        adc_oneshot_del_unit(s->adc_handle);
        free(s);
        return err;
    }

    ESP_LOGI(TAG, "Soil sensor initialized on ADC1 channel %d", adc_channel);
    *out_handle = s;
    return ESP_OK;
}

esp_err_t sensor_soil_read(sensor_soil_handle_t handle, float *moisture_pct)
{
    if (!handle || !moisture_pct) return ESP_ERR_INVALID_ARG;

    int raw = 0;
    esp_err_t err = adc_oneshot_read(handle->adc_handle, handle->channel,
                                     &raw);
    if (err != ESP_OK) return err;

    /* Map raw ADC value to percentage using calibration constants */
    float pct = (float)(MOLE_SOIL_AIR_VAL - raw) /
                (float)(MOLE_SOIL_AIR_VAL - MOLE_SOIL_WATER_VAL) * 100.0f;

    /* Clamp to 0–100% */
    if (pct < 0.0f)   pct = 0.0f;
    if (pct > 100.0f)  pct = 100.0f;

    *moisture_pct = pct;

    ESP_LOGD(TAG, "raw=%d  moisture=%.1f%%", raw, pct);
    return ESP_OK;
}
