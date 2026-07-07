#pragma once
#include "FreeRTOS.h"
#define vTaskDelete(a)
#define vTaskDelay(a)
#define xTaskCreate(a, b, c, d, e, f) pdTRUE
