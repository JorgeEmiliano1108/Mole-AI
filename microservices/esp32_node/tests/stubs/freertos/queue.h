#pragma once
#include "FreeRTOS.h"
#include <string.h>
#include <stdint.h>
#include <stdio.h>

/* Fixed-size circular buffer stub (supports up to 8 items of 8 bytes each) */
#define QSTUB_MAX_ITEMS 8
#define QSTUB_ITEM_SIZE 8

static uint8_t  s_qbuf[QSTUB_MAX_ITEMS][QSTUB_ITEM_SIZE];
static int      s_qhead = 0;
static int      s_qtail = 0;
static int      s_qcount = 0;
static int      s_qitem_sz = QSTUB_ITEM_SIZE;

static inline void qstub_reset(void)
{
    s_qhead = s_qtail = s_qcount = 0;
    s_qitem_sz = QSTUB_ITEM_SIZE;
    memset(s_qbuf, 0, sizeof(s_qbuf));
}

static inline QueueHandle_t xQueueCreate(unsigned uxItemCount, size_t uxItemSize)
{
    (void)uxItemCount;
    qstub_reset();
    if (uxItemSize < QSTUB_ITEM_SIZE) s_qitem_sz = (int)uxItemSize;
    return (QueueHandle_t)1;
}

static inline BaseType_t xQueueSend(QueueHandle_t xQueue, const void *pvItemToQueue, TickType_t xTicksToWait)
{
    (void)xQueue;
    (void)xTicksToWait;
    if (!pvItemToQueue || s_qitem_sz <= 0) return pdFALSE;
    if (s_qcount >= QSTUB_MAX_ITEMS) return pdFALSE;
    memcpy(s_qbuf[s_qtail], pvItemToQueue, (size_t)s_qitem_sz);
    s_qtail = (s_qtail + 1) % QSTUB_MAX_ITEMS;
    s_qcount++;
    return pdTRUE;
}

static inline BaseType_t xQueueReceive(QueueHandle_t xQueue, void *pvBuffer, TickType_t xTicksToWait)
{
    (void)xQueue;
    (void)xTicksToWait;
    if (!pvBuffer || s_qcount <= 0 || s_qitem_sz <= 0) return pdFALSE;
    memcpy(pvBuffer, s_qbuf[s_qhead], (size_t)s_qitem_sz);
    s_qhead = (s_qhead + 1) % QSTUB_MAX_ITEMS;
    s_qcount--;
    return pdTRUE;
}

static inline BaseType_t xQueueReset(QueueHandle_t xQueue)
{
    (void)xQueue;
    qstub_reset();
    return pdTRUE;
}
