#pragma once
#include "FreeRTOS.h"
#define xTimerCreate(a, b, c, d, e) ((TimerHandle_t)1)
#define xTimerStart(a, b) pdTRUE
#define vTimerDelete(a)
#define pdFALSE 0
