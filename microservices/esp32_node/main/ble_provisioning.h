#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <freertos/semphr.h>
#include "edge_frame.h"

extern SemaphoreHandle_t g_provision_sem;

void ble_provisioning_start(void);

/* Ventana live al despertar (spec gatt-fee2-spec.md §4). */
void ble_live_start(uint32_t window_s);

/* Publica la última trama FEE2 + notify best-effort. Retorna bytes o -1. */
int ble_fee2_publish(const edge_frame_t *frame);

#ifdef __cplusplus
}
#endif
