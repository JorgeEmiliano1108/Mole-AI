/*
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * state_machine.h — FSM declaration for Mole.AI Telemetry Node.
 *
 * VS2: 12 states, 19 events, transition-table driven.
 * All events arrive via a single FreeRTOS QueueHandle_t.
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ══════════════════════════════════════════════════════════════════════════
 *  States (12 nominal + 1 terminal)
 * ══════════════════════════════════════════════════════════════════════════ */
typedef enum {
    FSM_COLD_START,
    FSM_NVS_LOADING,
    FSM_PROVISIONING,
    FSM_WIFI_CONNECT,
    FSM_NTP_SYNC,
    FSM_SENSOR_INIT,
    FSM_TRANSPORT_CONNECTING,
    FSM_TELEMETRY_SENDING,
    FSM_TELEMETRY_DEGRADED,
    FSM_RECONNECTING,
    FSM_OFFLINE_BUFFER,
    FSM_DEEP_SLEEP,
    FSM_ERROR,
    FSM_STATE_COUNT,
} fsm_state_t;

/* ══════════════════════════════════════════════════════════════════════════
 *  Events (19)
 * ══════════════════════════════════════════════════════════════════════════ */
typedef enum {
    EV_NONE,
    EV_CREDS_FOUND,
    EV_CREDS_MISSING,
    EV_CREDS_SAVED,
    EV_WIFI_CONNECTED,
    EV_WIFI_DISCONNECT,
    EV_NTP_SYNCED,
    EV_NTP_TIMEOUT,
    EV_SENSOR_OK,
    EV_SENSOR_PARTIAL,
    EV_SENSOR_FAIL,
    EV_TRANSPORT_CONNECTED,
    EV_TRANSPORT_DISCONNECT,
    EV_TRANSPORT_AUTH_FAIL,
    EV_SEND_OK,
    EV_SEND_FAIL,
    EV_RECONNECT_EXCEEDED,
    EV_WIFI_RESTORED,
    EV_DEEP_SLEEP_WAKE,
    EV_ERROR,
    EV_EVENT_COUNT,
} fsm_event_t;

/* ══════════════════════════════════════════════════════════════════════════
 *  FSM Context
 * ══════════════════════════════════════════════════════════════════════════ */
typedef struct {
    fsm_state_t       current;
    QueueHandle_t     event_queue;
    fsm_state_t       last_persisted;     /* for NVS sync */
    int               reconnect_count;
    uint8_t           degraded_sensors;   /* bitmask, mirrors dg */
    uint8_t           buffered_count;     /* offline buffer samples */
} fsm_context_t;

/* ══════════════════════════════════════════════════════════════════════════
 *  API
 * ══════════════════════════════════════════════════════════════════════════ */

/**
 * @brief Create and initialise FSM context (allocates event queue).
 * @return Pointer to static context, or NULL.
 */
fsm_context_t* fsm_init(void);

/**
 * @brief Return the event queue handle (for event handlers to post).
 */
QueueHandle_t fsm_get_queue(fsm_context_t *ctx);

/**
 * @brief Core dispatch: look up (current_state × event) in transition table,
 *        run action, update state, call entry action if state changed.
 */
void fsm_dispatch(fsm_context_t *ctx, fsm_event_t ev);

/**
 * @brief FSM task — call this from xTaskCreate.
 *        Blocks on event queue, dispatches, loops until DEEP_SLEEP or ERROR.
 */
void fsm_task(void *arg);

/**
 * @brief Persist current state and reconnect_count to NVS.
 */
void fsm_persist_nvs(fsm_context_t *ctx);

/**
 * @brief Load persisted state from NVS.
 */
void fsm_load_nvs(fsm_context_t *ctx);

#ifdef __cplusplus
}
#endif
