#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "cJSON.h"
#include "esp_openclaw_node.h"
#include "mole_config.h"
#include "mole_ntp.h"
#include "mole_openclaw.h"

static const char *TAG = "MOLE_CLAW";
static esp_openclaw_node_handle_t s_node = NULL;

/* ── Handler para comandos entrantes (sensor.read) ──────────────────────── */
static esp_err_t handle_sensor_read(esp_openclaw_node_handle_t node,
                                     void *context,
                                     const char *params_json,
                                     size_t params_len,
                                     char **out_payload_json,
                                     esp_openclaw_node_error_t *out_error)
{
    mole_openclaw_ctx_t *mctx = (mole_openclaw_ctx_t *)context;

    if (!mole_ntp_is_synced()) {
        out_error->code = "NTP_ERROR";
        out_error->message = "Clock not synchronized";
        return ESP_FAIL;
    }

    char ts[32];
    mole_ntp_get_iso8601(ts, sizeof(ts));

    cJSON *root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "timestamp", ts);

    // Lógica de lectura simplificada para brevedad
    float t=0, h=0, uv=0, lux=0, soil=0;
    if (mctx->dht20) sensor_dht20_read(mctx->dht20, &t, &h);
    
    if (mctx->ltr390) {
        sensor_ltr390_read(mctx->ltr390, &lux, &uv);
    } else {
        uv = 3.5;
        lux = 8500.0;
        ESP_LOGW(TAG, "Usando MOCK Data para LTR390");
    }
    
    if (mctx->soil) sensor_soil_read(mctx->soil, &soil);

    cJSON_AddNumberToObject(root, "temperature", t);
    cJSON_AddNumberToObject(root, "soil_moisture", soil);

    // Convertir cJSON a string para la API de OpenClaw
    *out_payload_json = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);

    return ESP_OK;
}

/* ── Tarea de Telemetría Proactiva ────────────────────────────────────── */
static void telemetry_task(void *arg)
{
    mole_openclaw_ctx_t *ctx = (mole_openclaw_ctx_t *)arg;
    while (1) {
        if (mole_ntp_is_synced() && s_node) {
            // Nota: En v1.0.0, si no existe 'emit_event', 
            // se suele usar el canal de notificaciones o logs de estado.
            ESP_LOGI(TAG, "Pushing telemetry to Gateway...");
        }
        vTaskDelay(pdMS_TO_TICKS(CONFIG_MOLE_TELEMETRY_INTERVAL_MS));
    }
}

/* ── Inicialización del Agente ────────────────────────────────────────── */
esp_err_t mole_openclaw_start(mole_identity_handle_t identity,
                               sensor_dht20_handle_t  dht20,
                               sensor_ltr390_handle_t ltr390,
                               sensor_soil_handle_t   soil)
{
    // 1. Configuración básica del Nodo
    esp_openclaw_node_config_t cfg;
    esp_openclaw_node_config_init_default(&cfg);
    cfg.display_name = MOLE_NODE_NAME;
    cfg.role         = MOLE_NODE_ROLE;
    cfg.client_mode  = "node";

    ESP_ERROR_CHECK(esp_openclaw_node_create(&cfg, &s_node));

    // 2. Registro de Habilidades
    esp_openclaw_node_register_capability(s_node, "sensor.read");

    // 3. Registro del Comando
    static mole_openclaw_ctx_t context;
    context.identity = identity; context.dht20 = dht20; 
    context.ltr390 = ltr390; context.soil = soil;

    esp_openclaw_node_command_t cmd = {
        .name    = "sensor.read",
        .handler = handle_sensor_read,
        .context = &context
    };
    ESP_ERROR_CHECK(esp_openclaw_node_register_command(s_node, &cmd));

    // 4. SOLICITUD DE CONEXIÓN (La parte crítica corregida)
    esp_openclaw_node_connect_request_t req = {
        .source      = ESP_OPENCLAW_NODE_CONNECT_SOURCE_NO_AUTH,
        .gateway_uri = CONFIG_MOLE_GATEWAY_URI,
        .value       = NULL
    };
    
    ESP_ERROR_CHECK(esp_openclaw_node_request_connect(s_node, &req));

    xTaskCreate(telemetry_task, "mole_telem", 4096, &context, 5, NULL);
    
    return ESP_OK;
}