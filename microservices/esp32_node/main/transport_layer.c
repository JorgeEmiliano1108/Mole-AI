/*
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * transport_layer.c — HTTP REST transport for edge-batch telemetry upload.
 *
 * Send: POST /api/v1/sensor-data/edge-batch/
 * Auth: Authorization: Bearer <device_token>
 * Body: application/json (edge_frame_t compact payload)
 *
 * Events are pushed to a FreeRTOS QueueHandle_t for FSM consumption.
 */
#include <string.h>
#include <stdlib.h>
#include "esp_log.h"
#include "esp_http_client.h"
#include "transport_layer.h"

static const char *TAG = "TRANSPORT";

/* ── Internal handle ──────────────────────────────────────────────────────── */
struct transport_layer {
    transport_config_t    cfg;
    transport_callbacks_t cb;
    bool                  connected;
    bool                  initialized;
};

/* ── Helpers ──────────────────────────────────────────────────────────────── */

static void push_event(transport_handle_t *t, transport_event_type_t type,
                       int http_code, const char *response)
{
    if (!t || !t->cb.event_queue) return;
    transport_event_t ev;
    memset(&ev, 0, sizeof(ev));
    ev.type     = type;
    ev.http_code = http_code;
    if (response) {
        strncpy(ev.response, response, sizeof(ev.response) - 1);
    }
    xQueueSend(t->cb.event_queue, &ev, 0);
}

static esp_err_t http_event_handler(esp_http_client_event_t *evt)
{
    /* We handle response data in the caller via esp_http_client_read */
    return ESP_OK;
}

/* ── Public API ───────────────────────────────────────────────────────────── */

transport_handle_t* transport_init(const transport_config_t *cfg,
                                   const transport_callbacks_t *cb)
{
    if (!cfg || !cb) return NULL;

    transport_handle_t *t = calloc(1, sizeof(struct transport_layer));
    if (!t) return NULL;

    memcpy(&t->cfg, cfg, sizeof(transport_config_t));
    memcpy(&t->cb,  cb,  sizeof(transport_callbacks_t));
    t->connected    = false;
    t->initialized  = true;

    ESP_LOGI(TAG, "Transport initialized: %s", cfg->uri);
    return t;
}

transport_result_t transport_connect(transport_handle_t *t, int timeout_ms)
{
    transport_result_t result = {0};
    if (!t || !t->initialized) {
        result.status = TRANSPORT_ERROR;
        return result;
    }

    /*
     * For HTTP transport, "connect" is a lightweight HEAD request to verify
     * the endpoint is reachable and the token is accepted.
     */
    esp_http_client_config_t http_cfg = {
        .url                = t->cfg.uri,
        .method             = HTTP_METHOD_HEAD,
        .timeout_ms         = timeout_ms > 0 ? timeout_ms : t->cfg.timeout_ms,
        .event_handler      = http_event_handler,
        .skip_cert_common_name_check = true,  /* TODO: enable cert validation in production */
    };

    esp_http_client_handle_t client = esp_http_client_init(&http_cfg);
    if (!client) {
        result.status = TRANSPORT_ERROR;
        goto fail;
    }

    /* Set auth header */
    char auth_header[160];
    snprintf(auth_header, sizeof(auth_header), "Bearer %s", t->cfg.bearer_token);
    esp_http_client_set_header(client, "Authorization", auth_header);

    esp_err_t err = esp_http_client_perform(client);
    if (err == ESP_OK) {
        int status_code = esp_http_client_get_status_code(client);
        ESP_LOGI(TAG, "Connect check: HTTP %d", status_code);
        if (status_code == 200 || status_code == 201 || status_code == 204) {
            t->connected = true;
            push_event(t, TRANSPORT_EVT_CONNECTED, status_code, NULL);
            result.status = TRANSPORT_OK;
            result.http_code = status_code;
        } else if (status_code == 401) {
            push_event(t, TRANSPORT_EVT_AUTH_FAIL, status_code, "Unauthorized");
            result.status = TRANSPORT_AUTH_FAILED;
            result.http_code = status_code;
        } else {
            result.status = TRANSPORT_ERROR;
            result.http_code = status_code;
        }
    } else {
        ESP_LOGW(TAG, "Connect check failed: %s", esp_err_to_name(err));
        result.status = TRANSPORT_DISCONNECTED;
    }

    esp_http_client_cleanup(client);
    return result;

fail:
    push_event(t, TRANSPORT_EVT_ERROR, 0, "init failed");
    return result;
}

transport_result_t transport_send(transport_handle_t *t,
                                   const char *payload, int len)
{
    transport_result_t result = {0};
    if (!t || !t->initialized || !payload || len <= 0) {
        result.status = TRANSPORT_ERROR;
        return result;
    }

    esp_http_client_config_t http_cfg = {
        .url                = t->cfg.uri,
        .method             = HTTP_METHOD_POST,
        .timeout_ms         = t->cfg.timeout_ms,
        .event_handler      = http_event_handler,
        .skip_cert_common_name_check = true,
    };

    esp_http_client_handle_t client = esp_http_client_init(&http_cfg);
    if (!client) {
        result.status = TRANSPORT_ERROR;
        goto fail;
    }

    /* Headers */
    char auth_header[160];
    snprintf(auth_header, sizeof(auth_header), "Bearer %s", t->cfg.bearer_token);
    esp_http_client_set_header(client, "Authorization", auth_header);
    esp_http_client_set_header(client, "Content-Type", "application/json");

    /* Body */
    esp_http_client_set_post_field(client, payload, len);

    esp_err_t err = esp_http_client_perform(client);
    if (err == ESP_OK) {
        int status_code = esp_http_client_get_status_code(client);

        /* Read response body (truncated for diagnostics) */
        char resp_buf[128] = {0};
        int read_len = esp_http_client_read(client, resp_buf, sizeof(resp_buf) - 1);
        if (read_len > 0) {
            resp_buf[read_len] = '\0';
        }

        ESP_LOGI(TAG, "POST %s → HTTP %d", t->cfg.uri, status_code);

        result.http_code = status_code;
        strncpy(result.response, resp_buf, sizeof(result.response) - 1);

        if (status_code == 200 || status_code == 201) {
            result.status = TRANSPORT_OK;
            t->connected = true;
        } else if (status_code == 401) {
            result.status = TRANSPORT_AUTH_FAILED;
            t->connected = false;
            push_event(t, TRANSPORT_EVT_AUTH_FAIL, status_code, resp_buf);
        } else if (status_code == 429) {
            result.status = TRANSPORT_ERROR;  /* rate limit — caller should backoff */
            push_event(t, TRANSPORT_EVT_ERROR, status_code, resp_buf);
        } else {
            result.status = TRANSPORT_ERROR;
            push_event(t, TRANSPORT_EVT_ERROR, status_code, resp_buf);
        }
    } else {
        ESP_LOGW(TAG, "POST failed: %s", esp_err_to_name(err));
        result.status = TRANSPORT_DISCONNECTED;
        t->connected = false;
        push_event(t, TRANSPORT_EVT_DISCONNECTED, 0, esp_err_to_name(err));
    }

    esp_http_client_cleanup(client);
    return result;

fail:
    result.status = TRANSPORT_ERROR;
    return result;
}

void transport_disconnect(transport_handle_t *t)
{
    if (!t) return;
    t->connected = false;
    ESP_LOGI(TAG, "Transport disconnected");
}

bool transport_is_connected(const transport_handle_t *t)
{
    return t && t->connected;
}
