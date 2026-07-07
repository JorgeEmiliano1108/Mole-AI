#pragma once
#include "FreeRTOS.h"
static inline EventGroupHandle_t xEventGroupCreate(void) { return (EventGroupHandle_t)1; }
static inline void xEventGroupSetBits(EventGroupHandle_t xEventGroup, const BaseType_t uxBitsToSet) { (void)xEventGroup; (void)uxBitsToSet; }
static inline void xEventGroupClearBits(EventGroupHandle_t xEventGroup, const BaseType_t uxBitsToClear) { (void)xEventGroup; (void)uxBitsToClear; }
static inline BaseType_t xEventGroupWaitBits(EventGroupHandle_t xEventGroup, const BaseType_t uxBitsToWaitFor, const BaseType_t xClearOnExit, const BaseType_t xWaitForAllBits, TickType_t xTicksToWait) { (void)xEventGroup; (void)uxBitsToWaitFor; (void)xClearOnExit; (void)xWaitForAllBits; (void)xTicksToWait; return pdTRUE; }
