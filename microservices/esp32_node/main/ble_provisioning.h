#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <freertos/semphr.h>

extern SemaphoreHandle_t g_provision_sem;

void ble_provisioning_start(void);

#ifdef __cplusplus
}
#endif
