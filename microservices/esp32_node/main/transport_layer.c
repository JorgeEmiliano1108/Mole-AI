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
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_http_client.h"
#include "transport_layer.h"

static const char *TAG = "TRANSPORT";

/* Ancla CA de laboratorio embebida (EMBED_TXTFILES certs/lab_ca.pem, issue B-03).
 * Solo se usa cuando la URI es https; en http se ignora (flujo lab intacto). */
extern const char lab_ca_pem_start[] asm("_binary_lab_ca_pem_start");

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
        /* Guardrail TLS: CN validado contra el bundle + ancla lab (issue B-03).
         * En http el cert se ignora; en https sin handshake el perform falla
         * y el FSM cae a Fail-Safe/Store&Forward, nunca a plano. */
        .skip_cert_common_name_check = false,
        .cert_pem           = lab_ca_pem_start,
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

/* Backoff exponencial con jitter (±20 %): base_ms * 2^attempt. */
static void transport_backoff_delay(int base_ms, int attempt)
{
    uint32_t delay = (uint32_t)base_ms << (attempt > 5 ? 5 : attempt);
    if (delay > 30000) delay = 30000;
    int32_t jitter = (int32_t)(esp_random() % (delay / 5 + 1)) - (int32_t)(delay / 10);
    int32_t final_delay = (int32_t)delay + jitter;
    if (final_delay < 100) final_delay = 100;
    vTaskDelay(pdMS_TO_TICKS((uint32_t)final_delay));
}

transport_result_t transport_send(transport_handle_t *t,
                                   const char *payload, int len)
{
    transport_result_t result = {0};
    if (!t || !t->initialized || !payload || len <= 0) {
        result.status = TRANSPORT_ERROR;
        return result;
    }

    /* Issue C-08: los campos retry_* de t_cfg ahora se leen de verdad. */
    int attempts = t->cfg.retry_max > 0 ? t->cfg.retry_max : 1;
    int base_ms  = t->cfg.retry_backoff_base_ms > 0 ? t->cfg.retry_backoff_base_ms : 1000;

    int last_code = 0;
    char last_resp[128] = {0};
    bool transport_failed = false;

    for (int attempt = 0; attempt < attempts; attempt++) {
        esp_http_client_config_t http_cfg = {
            .url                = t->cfg.uri,
            .method             = HTTP_METHOD_POST,
            .timeout_ms         = t->cfg.timeout_ms,
            .event_handler      = http_event_handler,
            .skip_cert_common_name_check = false,
            .cert_pem           = lab_ca_pem_start,
        };

        esp_http_client_handle_t client = esp_http_client_init(&http_cfg);
        if (!client) {
            result.status = TRANSPORT_ERROR;
            transport_failed = true;
            break;
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

            ESP_LOGI(TAG, "POST %s → HTTP %d (attempt %d/%d)",
                     t->cfg.uri, status_code, attempt + 1, attempts);

            result.http_code = status_code;
            strncpy(result.response, resp_buf, sizeof(result.response) - 1);

            if (status_code == 200 || status_code == 201) {
                result.status = TRANSPORT_OK;
                t->connected = true;
                esp_http_client_cleanup(client);
                return result;
            }
            if (status_code == 401) {
                /* Auth no se reintenta: el token no se arregla solo. */
                result.status = TRANSPORT_AUTH_FAILED;
                t->connected = false;
                push_event(t, TRANSPORT_EVT_AUTH_FAIL, status_code, resp_buf);
                esp_http_client_cleanup(client);
                return result;
            }
            /* 429/5xx/otros: reintentable, se guarda el último para el evento final. */
            last_code = status_code;
            strncpy(last_resp, resp_buf, sizeof(last_resp) - 1);
            transport_failed = false;
        } else {
            ESP_LOGW(TAG, "POST failed: %s (attempt %d/%d)",
                     esp_err_to_name(err), attempt + 1, attempts);
            transport_failed = true;
        }

        esp_http_client_cleanup(client);

        if (attempt + 1 < attempts) {
            transport_backoff_delay(base_ms, attempt);
        }
    }

    /* Evento terminal único (antes se emitía por intento). */
    t->connected = false;
    if (transport_failed && last_code == 0) {
        result.status = TRANSPORT_DISCONNECTED;
        push_event(t, TRANSPORT_EVT_DISCONNECTED, 0, "send failed");
    } else {
        result.status = TRANSPORT_ERROR;
        push_event(t, TRANSPORT_EVT_ERROR, last_code, last_resp);
    }
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
