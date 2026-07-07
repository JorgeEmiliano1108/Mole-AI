#pragma once
#include "FreeRTOS.h"
static inline SemaphoreHandle_t xSemaphoreCreateBinary(void) {
    static int s_sem = 0;
    return (SemaphoreHandle_t)&s_sem;
}
static inline BaseType_t xSemaphoreTake(SemaphoreHandle_t xSemaphore, TickType_t xBlockTime) {
    (void)xSemaphore; (void)xBlockTime; return pdTRUE;
}
static inline BaseType_t xSemaphoreGive(SemaphoreHandle_t xSemaphore) {
    (void)xSemaphore; return pdTRUE;
}
