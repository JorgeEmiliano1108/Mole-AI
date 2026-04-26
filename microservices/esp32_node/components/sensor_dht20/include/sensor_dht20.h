/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * sensor_dht20.h — I2C driver for ASAIR DHT20 (Temperature + Humidity)
 *
 * I2C Address: 0x38 (fixed, no alternate)
 * Protocol:    Send trigger → wait 80ms → read 6 bytes + CRC
 * =============================================================================
 */
#pragma once

#include "esp_err.h"
#include "driver/i2c_master.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct sensor_dht20 *sensor_dht20_handle_t;

/**
 * @brief Initialize the DHT20 sensor on the given I2C bus.
 *
 * @param bus     I2C master bus handle
 * @param out_handle  Pointer to receive the sensor handle
 * @return ESP_OK on success
 */
esp_err_t sensor_dht20_init(i2c_master_bus_handle_t bus,
                            sensor_dht20_handle_t *out_handle);

/**
 * @brief Read temperature and humidity from the DHT20.
 *
 * @param handle      Sensor handle from sensor_dht20_init()
 * @param temperature Pointer to receive temperature in °C
 * @param humidity    Pointer to receive relative humidity in %
 * @return ESP_OK on success, ESP_ERR_TIMEOUT if sensor unresponsive
 */
esp_err_t sensor_dht20_read(sensor_dht20_handle_t handle,
                            float *temperature, float *humidity);

#ifdef __cplusplus
}
#endif
