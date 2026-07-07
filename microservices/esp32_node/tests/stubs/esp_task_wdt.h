#pragma once
#include "nvs.h"
static inline esp_err_t esp_task_wdt_delete(void *handle) { (void)handle; return ESP_OK; }
static inline void esp_task_wdt_reset(void) {}
