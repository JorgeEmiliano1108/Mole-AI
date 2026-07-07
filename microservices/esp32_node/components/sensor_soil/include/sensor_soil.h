/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * sensor_soil.h — ADC driver for capacitive soil moisture sensor
 * =============================================================================
 */
#pragma once

#include "esp_err.h"
#include "esp_adc/adc_oneshot.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct sensor_soil *sensor_soil_handle_t;

/**
 * @brief Initialize the capacitive soil moisture sensor via ADC oneshot.
 *
 * @param adc_handle   Shared ADC1 unit handle created externally
 * @param adc_channel  ADC1 channel number (e.g. 6 for GPIO34)
 * @param out_handle   Pointer to receive the sensor handle
 */
esp_err_t sensor_soil_init(adc_oneshot_unit_handle_t adc_handle, int adc_channel, sensor_soil_handle_t *out_handle);

/**
 * @brief Read soil moisture as a percentage (0–100%).
 *
 * Uses calibration constants MOLE_SOIL_AIR_VAL and MOLE_SOIL_WATER_VAL
 * from mole_config.h to map raw ADC to percentage.
 */
esp_err_t sensor_soil_read(sensor_soil_handle_t handle, float *moisture_pct);

/**
 * @brief Read raw ADC value (0–4095) for edge-batch payload.
 *
 * Use this when sending data to POST /api/v1/sensor-data/edge-batch/
 * which expects raw ADC values in s[].v.
 */
esp_err_t sensor_soil_read_raw(sensor_soil_handle_t handle, int *adc_raw);

#ifdef __cplusplus
}
#endif
