/*
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * transport_layer.h — Abstract transport interface for telemetry upload.
 *
 * Supports HTTP REST (primary) and WebSocket (legacy).
 * Events are pushed to a FreeRTOS QueueHandle_t for FSM consumption.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include "transport_config.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ── Result of a transport operation ──────────────────────────────────────── */
typedef enum {
    TRANSPORT_OK,            /* success */
    TRANSPORT_DISCONNECTED,  /* not connected */
    TRANSPORT_TIMEOUT,       /* request timed out */
    TRANSPORT_ERROR,         /* transient error (server 5xx, network) */
    TRANSPORT_AUTH_FAILED,   /* 401 — token invalid */
} transport_status_t;

typedef struct {
    transport_status_t status;
    int  http_code;          /* 0 if not HTTP, 200/201/400/401/429/500... */
    char response[256];      /* body truncado del servidor */
} transport_result_t;

/* ── Opaque handle ────────────────────────────────────────────────────────── */
typedef struct transport_layer transport_handle_t;

/* ── API ──────────────────────────────────────────────────────────────────── */

/**
 * @brief Initialize the transport layer.
 *
 * @param cfg  Static configuration (URI, token, timeouts). Must stay valid.
 * @param cb   Runtime callbacks (event queue). Must stay valid.
 * @return Handle or NULL on error.
 */
transport_handle_t* transport_init(const transport_config_t *cfg,
                                   const transport_callbacks_t *cb);

/**
 * @brief Connect to the remote endpoint.
 *
 * For HTTP: performs a lightweight handshake check (HEAD or minimal GET).
 * For WS: performs the WebSocket upgrade handshake.
 *
 * @param t          Transport handle.
 * @param timeout_ms Max time to wait for connection.
 * @return OK or error code.
 */
transport_result_t transport_connect(transport_handle_t *t, int timeout_ms);

/**
 * @brief Send a telemetry payload.
 *
 * @param t       Transport handle.
 * @param payload JSON string to send.
 * @param len     Length of payload (excluding null terminator).
 * @return Result with status and HTTP code.
 */
transport_result_t transport_send(transport_handle_t *t,
                                   const char *payload, int len);

/**
 * @brief Disconnect and release resources.
 */
void transport_disconnect(transport_handle_t *t);

/**
 * @brief Check if the transport is currently connected.
 */
bool transport_is_connected(const transport_handle_t *t);

#ifdef __cplusplus
}
#endif
