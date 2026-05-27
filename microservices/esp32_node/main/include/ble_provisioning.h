/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * ble_provisioning.h — BLE provisioning interface for the Mole.AI Telemetry Node.
 * =============================================================================
 */
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Start the BLE provisioning service (NimBLE).
 *
 * Advertises a custom GATT service that accepts Wi-Fi credentials
 * and a device token from a BLE central (mobile app / browser).
 * Signals g_provision_sem upon successful credential write.
 */
void ble_provisioning_start(void);

#ifdef __cplusplus
}
#endif
