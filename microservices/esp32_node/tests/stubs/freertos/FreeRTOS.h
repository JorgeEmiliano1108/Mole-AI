#pragma once
#include <stdint.h>
#include <stddef.h>
typedef void *QueueHandle_t;
typedef void *TaskHandle_t;
typedef void *SemaphoreHandle_t;
typedef void *EventGroupHandle_t;
typedef void *TimerHandle_t;
typedef long BaseType_t;
typedef unsigned long TickType_t;
#define pdTRUE 1
#define pdFALSE 0
#define pdMS_TO_TICKS(x) (x)
#define portMAX_DELAY (~0U)
#define BIT0 (1 << 0)
