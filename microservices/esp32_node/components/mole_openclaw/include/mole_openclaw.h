/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * mole_openclaw.h — OpenClaw agent lifecycle, capability registration, and
 *                    periodic telemetry emission via FreeRTOS task.
 * =============================================================================
 */
#pragma once

#include "esp_err.h"
#include "mole_identity.h"
#include "sensor_dht20.h"
#include "sensor_ltr390.h"
#include "sensor_soil.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Context structure shared between OpenClaw handlers and tasks.
 */
typedef struct {
    mole_identity_handle_t identity;
    sensor_dht20_handle_t  dht20;
    sensor_ltr390_handle_t ltr390;
    sensor_soil_handle_t   soil;
} mole_openclaw_ctx_t;

/**
 * @brief Initialize the OpenClaw agent, register capabilities, connect
 *        to the gateway, and launch the telemetry FreeRTOS task.
 *
 * This function:
 *   1. Creates the OpenClaw node with gateway URI from Kconfig
 *   2. Registers 4 capabilities (sensor.dht20.read, sensor.ltr390.read,
 *      sensor.soil.read, telemetry.report) — BEFORE connect
 *   3. Registers the sensor.read command handler
 *   4. Connects to the WebSocket gateway
 *   5. Spawns the telemetry_task on a FreeRTOS thread
 *
 * @return ESP_OK on success
 */
esp_err_t mole_openclaw_start(mole_identity_handle_t identity,
                               sensor_dht20_handle_t  dht20,
                               sensor_ltr390_handle_t ltr390,
                               sensor_soil_handle_t   soil);

#ifdef __cplusplus
}
#endif
