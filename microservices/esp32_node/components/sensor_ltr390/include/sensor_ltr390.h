/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * sensor_ltr390.h — I2C driver for Lite-On LTR-390UV-01 (ALS + UV Index)
 *
 * I2C Address: 0x53 (fixed)
 * Modes:       ALS (ambient light, lux) and UVS (ultraviolet index)
 * =============================================================================
 */
#pragma once

#include "esp_err.h"
#include "driver/i2c_master.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct sensor_ltr390 *sensor_ltr390_handle_t;

/**
 * @brief Initialize the LTR390 sensor on the given I2C bus.
 *        Configures gain=3, resolution=16-bit (ideal for outdoor sunlight).
 */
esp_err_t sensor_ltr390_init(i2c_master_bus_handle_t bus,
                             sensor_ltr390_handle_t *out_handle);

/**
 * @brief Read ambient light (lux) and UV index from the LTR390.
 *
 * Switches mode internally: ALS read → UVS read, each with ~100ms settling.
 * Conversion factors (gain=3x, 16-bit):
 *   lux = raw_als * 0.06
 *   uv_index = raw_uvs * 0.23
 *
 * @param handle   Sensor handle
 * @param lux      Pointer to receive ambient light in lux
 * @param uv_index Pointer to receive UV index
 */
esp_err_t sensor_ltr390_read(sensor_ltr390_handle_t handle,
                             float *lux, float *uv_index);

#ifdef __cplusplus
}
#endif
