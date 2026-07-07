/*
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * transport_config.h — Configuration types for the TransportLayer module.
 *
 * Communication between transport_layer and FSM is via FreeRTOS QueueHandle_t,
 * NOT direct function pointers, to avoid dangling callbacks after deep sleep.
 */
#pragma once

#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ── Transport type ───────────────────────────────────────────────────────── */
typedef enum {
    TRANSPORT_HTTP,     /* HTTP REST POST */
    TRANSPORT_WS        /* WebSocket (legacy) */
} transport_type_t;

/* ── Events sent from transport_layer to FSM via QueueHandle_t ────────────── */
typedef enum {
    TRANSPORT_EVT_CONNECTED,      /* connection established */
    TRANSPORT_EVT_DISCONNECTED,   /* connection dropped */
    TRANSPORT_EVT_ERROR,          /* transient error (will retry) */
    TRANSPORT_EVT_AUTH_FAIL,      /* 401 — token invalid, re-provisioning needed */
} transport_event_type_t;

typedef struct {
    transport_event_type_t type;
    int  http_code;                /* HTTP status code if applicable */
    char response[128];            /* body truncado del error, vacío si OK */
} transport_event_t;

/* ── Static configuration (set once at init) ──────────────────────────────── */
typedef struct {
    char uri[256];                 /* ej: "https://host/api/v1/sensor-data/edge-batch/" */
    char bearer_token[128];        /* Device.auth_token from NVS */
    int  timeout_ms;               /* request timeout */
    int  retry_max;                /* max retry attempts before OFFLINE_BUFFER */
    int  retry_backoff_base_ms;    /* base for exponential backoff */
} transport_config_t;

/* ── Runtime callbacks (communicated via FreeRTOS queue, not pointers) ────── */
typedef struct {
    QueueHandle_t event_queue;     /* FSM reads transport_event_t from this queue */
} transport_callbacks_t;

#ifdef __cplusplus
}
#endif
