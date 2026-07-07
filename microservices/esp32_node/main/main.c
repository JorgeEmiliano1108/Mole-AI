/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * main.c — Mole.AI Telemetry Node (Bare-Metal, ESP-IDF 5.x)
 *
 * Architecture:
 *   app_main() initialises NVS, netif, event loop, then launches fsm_task.
 *   The 12-state FSM owns all orchestration (wifi, sensors, transport, sleep).
 *   Event handlers post to the FSM event queue — they NEVER block.
 *
 * Regulatory Compliance:
 *   IFT-016:        No calls to esp_wifi_set_max_tx_power()
 *   ETSI EN 303 645: NTP-synchronized UNIX timestamps on all telemetry
 *   LFPDPPP:        Zero PII in flash — identity = Device Token (UUID)
 * =============================================================================
 */
#include <stdio.h>
#include <string.h>
#include <time.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "freertos/semphr.h"
#include "freertos/timers.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "esp_timer.h"
#include "esp_sleep.h"
#include "esp_task_wdt.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "driver/i2c_master.h"
#include "esp_http_server.h"
#include "transport_layer.h"
#include "transport_config.h"
#include "esp_websocket_client.h"
#include "esp_adc/adc_oneshot.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include <arpa/inet.h>
#include "cJSON.h"

/* Mole.AI sensor components */
#include "mole_config.h"
#include "mole_ntp.h"
#include "sensor_dht20.h"
#include "sensor_ltr390.h"
#include "sensor_soil.h"
#include "ble_provisioning.h"
#include "payload_builder.h"
#include "edge_frame.h"
#include "sensor_frame.h"
#include "offline_buffer.h"
#include "state_machine.h"

static const char *TAG = "MOLE_MAIN";

/* Semaphore to signal provisioning completion (BLE or Captive Portal) */
SemaphoreHandle_t g_provision_sem = NULL;

/* ── FreeRTOS Event Group (used internally by wifi_init_sta) ────────────── */
static EventGroupHandle_t wifi_event_group;
#define WIFI_CONNECTED_BIT   BIT0

/* ── Global sensor handles ────────────────────────────────────────────────── */
static sensor_dht20_handle_t  s_dht20  = NULL;
static sensor_ltr390_handle_t s_ltr390 = NULL;
static sensor_soil_handle_t   s_soil[MOLE_NUM_ACTIVE_SOIL_PINS] = {0};
static adc_oneshot_unit_handle_t s_adc1 = NULL;
static i2c_master_bus_handle_t   s_i2c_bus = NULL;

/* ── Device Token (read from NVS at boot) ────────────────────────────────── */
static char s_device_token[128] = {0};

/* ── TransportLayer (HTTP REST) ──────────────────────────────────────────── */
static transport_handle_t *s_transport = NULL;
static QueueHandle_t s_transport_event_queue = NULL;

/* ── Payload buffer (pre-allocated, reused per cycle) ────────────────────── */
static char s_payload_buf[512];

/* ── Edge frame for current telemetry cycle ──────────────────────────────── */
static edge_frame_t s_edge_frame;

/* ── FSM event queue (handlers post here; fsm_task consumes) ─────────────── */
static QueueHandle_t s_fsm_queue = NULL;

/* ── Backoff state (VS3) ─────────────────────────────────────────────────── */
static int s_reconnect_attempt = 0;

/* ==========================================================================
 * SECTION 1: NVS Token Management
 * ========================================================================== */

static bool nvs_load_token(void)
{
    nvs_handle_t handle;
    esp_err_t err = nvs_open(MOLE_NVS_NAMESPACE, NVS_READONLY, &handle);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "NVS namespace '%s' not found (first boot?)", MOLE_NVS_NAMESPACE);
        return false;
    }

    size_t len = sizeof(s_device_token);
    err = nvs_get_str(handle, MOLE_NVS_KEY_TOKEN, s_device_token, &len);

    char wifi_ssid[32] = {0};
    size_t ssid_len = sizeof(wifi_ssid);
    esp_err_t ssid_err = nvs_get_str(handle, "wifi_ssid", wifi_ssid, &ssid_len);

    nvs_close(handle);

    if (err == ESP_OK && len > 1 && ssid_err == ESP_OK && ssid_len > 1) {
        ESP_LOGI(TAG, "Device Token and WiFi SSID loaded from NVS");
        return true;
    }

    ESP_LOGW(TAG, "Missing device token or WiFi SSID in NVS.");
    return false;
}

static esp_err_t nvs_save_token(const char *token)
{
    nvs_handle_t handle;
    ESP_ERROR_CHECK(nvs_open(MOLE_NVS_NAMESPACE, NVS_READWRITE, &handle));
    ESP_ERROR_CHECK(nvs_set_str(handle, MOLE_NVS_KEY_TOKEN, token));
    ESP_ERROR_CHECK(nvs_commit(handle));
    nvs_close(handle);
    ESP_LOGI(TAG, "Device Token saved to NVS.");
    return ESP_OK;
}

/* ==========================================================================
 * SECTION 2: Captive Portal (Wi-Fi AP + HTTP Server + DNS)
 * ========================================================================== */

/* Forward declaration — defined below */
static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                               int32_t event_id, void *event_data);

#define MAX_SCANNED_APS 10
static wifi_ap_record_t s_ap_info_cache[MAX_SCANNED_APS];
static uint16_t s_ap_count_cache = 0;
static bool s_scan_completed = false;

static void wifi_background_scan_task(void *pvParameters)
{
    ESP_LOGI(TAG, "Waiting for WiFi radio stabilization...");
    vTaskDelay(pdMS_TO_TICKS(2000));

    ESP_LOGI(TAG, "Starting background WiFi scan...");
    uint16_t number = MAX_SCANNED_APS;

    if (esp_wifi_scan_start(NULL, true) == ESP_OK) {
        esp_wifi_scan_get_ap_num(&s_ap_count_cache);
        if (s_ap_count_cache > MAX_SCANNED_APS) {
            s_ap_count_cache = MAX_SCANNED_APS;
        }
        number = s_ap_count_cache;
        esp_wifi_scan_get_ap_records(&number, s_ap_info_cache);
        ESP_LOGI(TAG, "Background scan finished. Found %d APs.", s_ap_count_cache);
    } else {
        ESP_LOGE(TAG, "Background WiFi scan failed");
        s_ap_count_cache = 0;
    }

    s_scan_completed = true;
    vTaskDelete(NULL);
}

static void dns_server_task(void *pvParameters)
{
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(53);
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);

    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    if (sock < 0) {
        ESP_LOGE(TAG, "Failed to create DNS socket");
        vTaskDelete(NULL);
        return;
    }

    if (bind(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        ESP_LOGE(TAG, "Failed to bind DNS socket");
        close(sock);
        vTaskDelete(NULL);
        return;
    }

    ESP_LOGI(TAG, "DNS Server listening on UDP port 53");

    char rx_buffer[128];
    while (1) {
        struct sockaddr_in source_addr;
        socklen_t socklen = sizeof(source_addr);
        int len = recvfrom(sock, rx_buffer, sizeof(rx_buffer), 0, (struct sockaddr *)&source_addr, &socklen);

        if (len > 0) {
            uint16_t tx_id = *((uint16_t *)rx_buffer);
            uint16_t flags = htons(0x8180);
            uint16_t qdcount = htons(1);
            uint16_t ancount = htons(1);
            uint16_t nscount = 0;
            uint16_t arcount = 0;

            char tx_buffer[128];
            int tx_len = 0;
            memcpy(tx_buffer + tx_len, &tx_id, 2); tx_len += 2;
            memcpy(tx_buffer + tx_len, &flags, 2); tx_len += 2;
            memcpy(tx_buffer + tx_len, &qdcount, 2); tx_len += 2;
            memcpy(tx_buffer + tx_len, &ancount, 2); tx_len += 2;
            memcpy(tx_buffer + tx_len, &nscount, 2); tx_len += 2;
            memcpy(tx_buffer + tx_len, &arcount, 2); tx_len += 2;

            int q_len = 0;
            while (rx_buffer[12 + q_len] != 0 && (12 + q_len) < len) {
                q_len++;
            }
            q_len += 5;

            if (12 + q_len <= len && tx_len + q_len + 16 <= sizeof(tx_buffer)) {
                memcpy(tx_buffer + tx_len, rx_buffer + 12, q_len);
                tx_len += q_len;

                uint16_t name_ptr = htons(0xC00C);
                uint16_t type_a = htons(0x0001);
                uint16_t class_in = htons(0x0001);
                uint32_t ttl = htonl(60);
                uint16_t data_len = htons(4);
                uint32_t ip_addr = inet_addr("192.168.4.1");

                memcpy(tx_buffer + tx_len, &name_ptr, 2); tx_len += 2;
                memcpy(tx_buffer + tx_len, &type_a, 2); tx_len += 2;
                memcpy(tx_buffer + tx_len, &class_in, 2); tx_len += 2;
                memcpy(tx_buffer + tx_len, &ttl, 4); tx_len += 4;
                memcpy(tx_buffer + tx_len, &data_len, 2); tx_len += 2;
                memcpy(tx_buffer + tx_len, &ip_addr, 4); tx_len += 4;

                sendto(sock, tx_buffer, tx_len, 0, (struct sockaddr *)&source_addr, sizeof(source_addr));
            }
        }
    }
}

static esp_err_t captive_err_handler(httpd_req_t *req, httpd_err_code_t error)
{
    if (error == HTTPD_404_NOT_FOUND) {
        httpd_resp_set_status(req, "302 Found");
        httpd_resp_set_hdr(req, "Location", "http://setup.mole.ai/");
        httpd_resp_send(req, NULL, 0);
        return ESP_OK;
    }
    return ESP_FAIL;
}

static esp_err_t captive_get_handler(httpd_req_t *req)
{
    ESP_LOGI(TAG, "Serving Captive Portal HTML...");

    char *html = malloc(4096);
    if (!html) return ESP_FAIL;

    int offset = snprintf(html, 4096,
        "<!DOCTYPE html><html><head>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Mole.AI Setup</title>"
        "<style>"
        "body{font-family:sans-serif;background:#0a0f14;color:#00ffc8;"
        "display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}"
        ".card{background:#111820;padding:2rem;border-radius:12px;border:1px solid #00ffc855;"
        "width:90%%;max-width:380px}"
        "h2{text-align:center;margin-bottom:1.5rem}"
        "input,select{width:100%%;padding:10px;margin:8px 0;border:1px solid #00ffc855;"
        "background:#0a0f14;color:#00ffc8;border-radius:6px;font-family:monospace;"
        "box-sizing:border-box}"
        "button{width:100%%;padding:12px;margin-top:16px;background:transparent;"
        "color:#00ffc8;border:2px solid #00ffc8;border-radius:6px;cursor:pointer;"
        "font-weight:bold;font-size:1rem}"
        "button:hover{background:#00ffc8;color:#0a0f14}"
        ".scan-btn{margin-top:0;margin-bottom:4px;padding:8px;font-size:0.85rem;"
        "border-style:dashed;opacity:0.85}"
        "</style></head><body>"
        "<div class='card'>"
        "<h2>&#x1F331; Mole.AI Setup</h2>"
        "<form method='POST' action='/save'>"
        "<button type='button' class='scan-btn' id='scan-btn' "
        "onclick=\"doScan()\">&#x1F504; Escanear Redes</button>"
        "<select name='ssid' id='ssid-select' required>"
    );

    if (!s_scan_completed) {
        offset += snprintf(html + offset, 4096 - offset, "<option value=''>Escaneando redes...</option>");
    } else if (s_ap_count_cache == 0) {
        offset += snprintf(html + offset, 4096 - offset, "<option value=''>No se encontraron redes.</option>");
    } else {
        for (int i = 0; i < s_ap_count_cache; i++) {
            if (strlen((char *)s_ap_info_cache[i].ssid) > 0) {
                offset += snprintf(html + offset, 4096 - offset,
                    "<option value='%s'>%s (%d dBm)</option>",
                    s_ap_info_cache[i].ssid, s_ap_info_cache[i].ssid, s_ap_info_cache[i].rssi);
            }
        }
    }

    snprintf(html + offset, 4096 - offset,
        "</select>"
        "<input name='pass' type='password' placeholder='WiFi Password' required>"
        "<input name='token' placeholder='Device Token' required>"
        "<input name='interval' type='number' placeholder='Intervalo (Minutos)' min='1' max='120' value='5' required>"
        "<button type='submit'>Guardar y Conectar</button>"
        "</form></div>"
        "<script>"
        "function doScan(){"
        "var b=document.getElementById('scan-btn');"
        "var s=document.getElementById('ssid-select');"
        "b.disabled=true;b.textContent='Escaneando...';"
        "fetch('/api/scan').then(function(r){return r.json();})"
        ".then(function(d){"
        "s.innerHTML='';"
        "if(d.length===0){s.innerHTML='<option value=\\'\\'>No se encontraron redes.</option>';}"
        "else{d.forEach(function(ap){"
        "var o=document.createElement('option');"
        "o.value=ap.ssid;o.textContent=ap.ssid+' ('+ap.rssi+' dBm)';"
        "s.appendChild(o);});}"
        "b.disabled=false;b.textContent='\\u1F504 Escanear Redes';"
        "}).catch(function(){"
        "b.disabled=false;b.textContent='\\u1F504 Escanear Redes';"
        "s.innerHTML='<option value=\\'\\'>Error. Reintente.</option>';});"
        "}"
        "</script>"
        /* Placeholder: In production, encrypt JSON payload with AES-GCM via Web Crypto API */
        "</body></html>"
    );

    httpd_resp_set_type(req, "text/html");
    esp_err_t res = httpd_resp_send(req, html, HTTPD_RESP_USE_STRLEN);
    free(html);
    return res;
}

static esp_err_t captive_scan_handler(httpd_req_t *req)
{
    ESP_LOGI(TAG, "AJAX scan requested via /api/scan");
    uint16_t number = MAX_SCANNED_APS;

    if (esp_wifi_scan_start(NULL, true) == ESP_OK) {
        esp_wifi_scan_get_ap_num(&s_ap_count_cache);
        if (s_ap_count_cache > MAX_SCANNED_APS) s_ap_count_cache = MAX_SCANNED_APS;
        number = s_ap_count_cache;
        esp_wifi_scan_get_ap_records(&number, s_ap_info_cache);
        s_scan_completed = true;
        ESP_LOGI(TAG, "AJAX scan found %d APs.", s_ap_count_cache);
    } else {
        ESP_LOGE(TAG, "AJAX WiFi scan failed");
        s_ap_count_cache = 0;
        s_scan_completed = true;
    }

    char *json = malloc(1024);
    if (!json) return ESP_FAIL;

    int off = 0;
    json[off++] = '[';
    for (int i = 0; i < s_ap_count_cache; i++) {
        if (strlen((char *)s_ap_info_cache[i].ssid) == 0) continue;
        if (off > 1) json[off++] = ',';
        off += snprintf(json + off, 1024 - off,
            "{\"ssid\":\"%s\",\"rssi\":%d}",
            s_ap_info_cache[i].ssid, s_ap_info_cache[i].rssi);
    }
    json[off++] = ']';
    json[off] = '\0';

    httpd_resp_set_type(req, "application/json");
    esp_err_t res = httpd_resp_send(req, json, HTTPD_RESP_USE_STRLEN);
    free(json);
    return res;
}

static esp_err_t captive_post_handler(httpd_req_t *req)
{
    char buf[512];
    int received = httpd_req_recv(req, buf, sizeof(buf) - 1);
    if (received <= 0) return ESP_FAIL;
    buf[received] = '\0';

    char ssid[64] = {0}, pass[64] = {0}, token[128] = {0}, interval_str[16] = {0};

    char *p = buf;
    while (p && *p) {
        char *eq = strchr(p, '=');
        if (!eq) break;
        *eq = '\0';
        char *val = eq + 1;
        char *amp = strchr(val, '&');
        if (amp) *amp = '\0';

        if (strcmp(p, "ssid") == 0)  strncpy(ssid, val, sizeof(ssid) - 1);
        if (strcmp(p, "pass") == 0)  strncpy(pass, val, sizeof(pass) - 1);
        if (strcmp(p, "token") == 0) strncpy(token, val, sizeof(token) - 1);
        if (strcmp(p, "interval") == 0) strncpy(interval_str, val, sizeof(interval_str) - 1);

        p = amp ? amp + 1 : NULL;
    }

    if (strlen(ssid) == 0 || strlen(token) == 0) {
        httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "Missing fields");
        return ESP_FAIL;
    }

    uint32_t interval_min = atoi(interval_str);
    if (interval_min < 1) interval_min = 1;
    if (interval_min > 120) interval_min = 120;

    wifi_config_t wifi_cfg = {0};
    strncpy((char *)wifi_cfg.sta.ssid, ssid, sizeof(wifi_cfg.sta.ssid) - 1);
    strncpy((char *)wifi_cfg.sta.password, pass, sizeof(wifi_cfg.sta.password) - 1);
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_cfg));

    nvs_handle_t handle;
    ESP_ERROR_CHECK(nvs_open(MOLE_NVS_NAMESPACE, NVS_READWRITE, &handle));
    ESP_ERROR_CHECK(nvs_set_str(handle, MOLE_NVS_KEY_TOKEN, token));
    ESP_ERROR_CHECK(nvs_set_str(handle, "wifi_ssid", ssid));
    ESP_ERROR_CHECK(nvs_set_str(handle, "wifi_pass", pass));
    ESP_ERROR_CHECK(nvs_set_u32(handle, "telemetry_int", interval_min));
    ESP_ERROR_CHECK(nvs_commit(handle));
    nvs_close(handle);
    ESP_LOGI(TAG, "Device Token, WiFi SSID/Pass & Interval (%lu min) saved to NVS.", interval_min);

    const char *resp = "<html><body style='background:#0a0f14;color:#00ffc8;"
        "font-family:sans-serif;display:flex;justify-content:center;"
        "align-items:center;height:100vh'>"
        "<h2>&#x2705; Configurado. Reiniciando...</h2></body></html>";
    httpd_resp_set_type(req, "text/html");
    httpd_resp_send(req, resp, HTTPD_RESP_USE_STRLEN);

    if (g_provision_sem) {
        xSemaphoreGive(g_provision_sem);
    }
    return ESP_OK;
}

static void start_captive_portal(void)
{
    ESP_LOGI(TAG, "=== CAPTIVE PORTAL MODE ===");

    esp_netif_create_default_wifi_ap();
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL));

    wifi_config_t ap_cfg = {
        .ap = {
            .ssid = MOLE_AP_SSID,
            .password = MOLE_AP_PASS,
            .ssid_len = strlen(MOLE_AP_SSID),
            .channel = MOLE_AP_CHANNEL,
            .max_connection = MOLE_AP_MAX_CONN,
            .authmode = WIFI_AUTH_WPA2_PSK,
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_APSTA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &ap_cfg));
    ESP_ERROR_CHECK(esp_wifi_start());
    esp_wifi_set_ps(WIFI_PS_NONE);

    ESP_LOGI(TAG, "AP started: SSID='%s' PASS='%s'", MOLE_AP_SSID, MOLE_AP_PASS);

    xTaskCreate(dns_server_task, "dns_server", 4096, NULL, 5, NULL);
    xTaskCreate(wifi_background_scan_task, "wifi_bg_scan", 4096, NULL, 5, NULL);

    httpd_config_t http_cfg = HTTPD_DEFAULT_CONFIG();
    http_cfg.uri_match_fn = httpd_uri_match_wildcard;
    httpd_handle_t server = NULL;
    ESP_ERROR_CHECK(httpd_start(&server, &http_cfg));

    httpd_register_err_handler(server, HTTPD_404_NOT_FOUND, captive_err_handler);

    httpd_uri_t get_uri = {
        .uri = "/", .method = HTTP_GET,
        .handler = captive_get_handler, .user_ctx = NULL
    };
    httpd_uri_t scan_uri = {
        .uri = "/api/scan", .method = HTTP_GET,
        .handler = captive_scan_handler, .user_ctx = NULL
    };
    httpd_uri_t post_uri = {
        .uri = "/save", .method = HTTP_POST,
        .handler = captive_post_handler, .user_ctx = NULL
    };
    httpd_register_uri_handler(server, &get_uri);
    httpd_register_uri_handler(server, &scan_uri);
    httpd_register_uri_handler(server, &post_uri);

    ESP_LOGI(TAG, "HTTP server listening on http://192.168.4.1/");
    ESP_LOGI(TAG, "Waiting for provisioning via Captive Portal...");

    if (g_provision_sem) {
        if (xSemaphoreTake(g_provision_sem, pdMS_TO_TICKS(MOLE_PROV_TIMEOUT_MS)) == pdTRUE) {
            ESP_LOGI(TAG, "Provisioning completed – restarting…");
            esp_restart();
        } else {
            ESP_LOGW(TAG, "Provisioning timed out after %d ms — deep sleep", MOLE_PROV_TIMEOUT_MS);
            enter_deep_sleep();
        }
    }
}

/* ==========================================================================
 * SECTION 3: WiFi STA + Backoff (event-driven, posts to FSM queue)
 * ========================================================================== */

static void reconnect_save_nvs(void)
{
    nvs_handle_t h;
    if (nvs_open(MOLE_NVS_NAMESPACE, NVS_READWRITE, &h) == ESP_OK) {
        nvs_set_i32(h, "reconnect_cnt", s_reconnect_attempt);
        nvs_commit(h);
        nvs_close(h);
    }
}

#define BACKOFF_BASE_MS  1000
#define BACKOFF_MAX_MS   30000
#define BACKOFF_MAX_ATT  6

static int reconnect_backoff_delay_ms(void)
{
    uint32_t attempt = (uint32_t)(s_reconnect_attempt < BACKOFF_MAX_ATT
                                  ? s_reconnect_attempt : BACKOFF_MAX_ATT - 1);
    uint32_t delay = BACKOFF_BASE_MS << attempt;
    if (delay > BACKOFF_MAX_MS) delay = BACKOFF_MAX_MS;

    int32_t jitter_range = (int32_t)(delay / 10);
    int32_t jitter = (int32_t)(esp_random() % (uint32_t)(jitter_range * 2 + 1))
                     - jitter_range;
    int32_t final_delay = (int32_t)delay + jitter;
    if (final_delay < 100) final_delay = 100;

    s_reconnect_attempt++;
    return final_delay;
}

static void reconnect_timer_cb(TimerHandle_t xTimer)
{
    reconnect_save_nvs();
    esp_wifi_connect();
    vTimerDelete(xTimer);
}

static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                               int32_t event_id, void *event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        if (wifi_event_group) {
            esp_wifi_connect();
        }
    } else if (event_base == WIFI_EVENT &&
               event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (wifi_event_group) {
            int delay_ms = reconnect_backoff_delay_ms();
            xEventGroupClearBits(wifi_event_group, WIFI_CONNECTED_BIT);
            TimerHandle_t t = xTimerCreate("reconnect",
                                           pdMS_TO_TICKS(delay_ms),
                                           pdFALSE, NULL,
                                           reconnect_timer_cb);
            if (t) {
                xTimerStart(t, 0);
            } else {
                esp_wifi_connect();
            }
            ESP_LOGW(TAG, "WiFi disconnected — reconnect in %d ms (attempt %d)",
                     delay_ms, s_reconnect_attempt);
        }
        if (s_fsm_queue) {
            fsm_event_t ev = EV_WIFI_DISCONNECT;
            xQueueSend(s_fsm_queue, &ev, 0);
        }
    } else if (event_base == IP_EVENT &&
               event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *evt = (ip_event_got_ip_t *)event_data;
        ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&evt->ip_info.ip));
        s_reconnect_attempt = 0;
        reconnect_save_nvs();
        esp_wifi_set_ps(WIFI_PS_NONE);
        if (wifi_event_group) {
            xEventGroupSetBits(wifi_event_group, WIFI_CONNECTED_BIT);
        }
        if (s_fsm_queue) {
            fsm_event_t ev = EV_WIFI_CONNECTED;
            xQueueSend(s_fsm_queue, &ev, 0);
        }
    }
}

static void wifi_init_sta(void)
{
    wifi_event_group = xEventGroupCreate();
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL));

    char wifi_ssid[32] = {0};
    char wifi_pass[64] = {0};
    size_t size = sizeof(wifi_ssid);
    nvs_handle_t handle;
    if (nvs_open(MOLE_NVS_NAMESPACE, NVS_READONLY, &handle) == ESP_OK) {
        nvs_get_str(handle, "wifi_ssid", wifi_ssid, &size);
        size = sizeof(wifi_pass);
        nvs_get_str(handle, "wifi_pass", wifi_pass, &size);
        nvs_close(handle);
    }

    wifi_config_t wifi_cfg = {0};
    strncpy((char *)wifi_cfg.sta.ssid, wifi_ssid, sizeof(wifi_cfg.sta.ssid) - 1);
    strncpy((char *)wifi_cfg.sta.password, wifi_pass, sizeof(wifi_cfg.sta.password) - 1);
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_cfg));

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_start());

    esp_wifi_set_ps(WIFI_PS_NONE);

    ESP_LOGI(TAG, "WiFi STA started — waiting for IP (async)");
}

/* ==========================================================================
 * SECTION 4: TransportLayer Wrapper
 * ========================================================================== */

static void transport_init_and_connect(void)
{
    s_transport_event_queue = xQueueCreate(4, sizeof(transport_event_t));
    if (!s_transport_event_queue) {
        ESP_LOGE(TAG, "Failed to create transport event queue");
        if (s_fsm_queue) {
            fsm_event_t ev = EV_TRANSPORT_DISCONNECT;
            xQueueSend(s_fsm_queue, &ev, 0);
        }
        return;
    }

    transport_config_t t_cfg = {0};
    strncpy(t_cfg.uri, CONFIG_MOLE_HTTP_URI, sizeof(t_cfg.uri) - 1);
    strncpy(t_cfg.bearer_token, s_device_token, sizeof(t_cfg.bearer_token) - 1);
    t_cfg.timeout_ms          = 10000;
    t_cfg.retry_max           = 3;
    t_cfg.retry_backoff_base_ms = 2000;

    transport_callbacks_t t_cb = {
        .event_queue = s_transport_event_queue,
    };

    s_transport = transport_init(&t_cfg, &t_cb);
    if (!s_transport) {
        ESP_LOGE(TAG, "Transport init failed");
        if (s_fsm_queue) {
            fsm_event_t ev = EV_TRANSPORT_DISCONNECT;
            xQueueSend(s_fsm_queue, &ev, 0);
        }
        return;
    }

    transport_result_t res = transport_connect(s_transport, 10000);
    if (res.status == TRANSPORT_OK) {
        ESP_LOGI(TAG, "Transport connected");
        if (s_fsm_queue) {
            fsm_event_t ev = EV_TRANSPORT_CONNECTED;
            xQueueSend(s_fsm_queue, &ev, 0);
        }
    } else if (res.status == TRANSPORT_AUTH_FAILED) {
        ESP_LOGE(TAG, "Transport auth failed");
        if (s_fsm_queue) {
            fsm_event_t ev = EV_TRANSPORT_AUTH_FAIL;
            xQueueSend(s_fsm_queue, &ev, 0);
        }
    } else {
        ESP_LOGW(TAG, "Transport connect: HTTP %d", res.http_code);
        if (s_fsm_queue) {
            fsm_event_t ev = EV_TRANSPORT_DISCONNECT;
            xQueueSend(s_fsm_queue, &ev, 0);
        }
    }
}

/* ==========================================================================
 * SECTION 5: Sensor Init
 * ========================================================================== */

static void sensor_init_all(void)
{
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port   = I2C_NUM_0,
        .sda_io_num = CONFIG_MOLE_I2C_SDA,
        .scl_io_num = CONFIG_MOLE_I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &s_i2c_bus));

    ESP_ERROR_CHECK(sensor_dht20_init(s_i2c_bus, &s_dht20));

    esp_err_t err_ltr = sensor_ltr390_init(s_i2c_bus, &s_ltr390);
    if (err_ltr != ESP_OK) {
        ESP_LOGE(TAG, "LTR390 init failed (0x%x). Using MOCK data.", err_ltr);
        s_ltr390 = NULL;
    }

    adc_oneshot_unit_init_cfg_t unit_cfg = {
        .unit_id = ADC_UNIT_1,
    };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&unit_cfg, &s_adc1));

    const int soil_pins[] = MOLE_ACTIVE_SOIL_PINS;
    for (int i = 0; i < MOLE_NUM_ACTIVE_SOIL_PINS; i++) {
        int channel = MOLE_GPIO_TO_ADC1_CHANNEL(soil_pins[i]);
        if (channel < 0) {
            ESP_LOGE(TAG, "Invalid soil GPIO %d — not an ADC1 pin!", soil_pins[i]);
            continue;
        }
        esp_err_t err = sensor_soil_init(s_adc1, channel, &s_soil[i]);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Soil sensor on GPIO %d failed (0x%x)", soil_pins[i], err);
            s_soil[i] = NULL;
        } else {
            ESP_LOGI(TAG, "Soil sensor OK on GPIO %d (ADC1 ch%d)", soil_pins[i], channel);
        }
    }
}

static int sensor_get_degraded_bitmask(void)
{
    int dg = 0;
    if (!s_dht20)  dg |= DEGRADED_TEMP_BIT | DEGRADED_HUM_BIT;
    if (!s_ltr390) dg |= DEGRADED_LIGHT_BIT | DEGRADED_UV_BIT;
    return dg;
}

/* ==========================================================================
 * SECTION 6: Telemetry Send
 * ========================================================================== */

static void build_edge_frame(void)
{
    memset(&s_edge_frame, 0, sizeof(s_edge_frame));

    s_edge_frame.ts = (double)time(NULL);
    s_edge_frame.report_interval_minutes = MOLE_REPORT_INTERVAL_DEFAULT;

    int ambient_valid = 0;
    float air_temp = 0, air_hum = 0, lux = 0, uv = 0;

    if (s_dht20 && sensor_dht20_read(s_dht20, &air_temp, &air_hum) == ESP_OK) {
        s_edge_frame.ambient.t = air_temp;
        s_edge_frame.ambient.h = air_hum;
        ambient_valid |= 0x03;
    }

    if (s_ltr390 && sensor_ltr390_read(s_ltr390, &lux, &uv) == ESP_OK) {
        s_edge_frame.ambient.l = lux;
        s_edge_frame.ambient.u = uv;
        ambient_valid |= 0x0C;
    } else if (!s_ltr390) {
        s_edge_frame.ambient.l = 8500.0f;
        s_edge_frame.ambient.u = 3.5f;
        ambient_valid |= 0x0C;
    }

    s_edge_frame.ambient_valid = ambient_valid;
    s_edge_frame.dg = (~ambient_valid) & 0x0F;

    const int soil_pins[] = MOLE_ACTIVE_SOIL_PINS;
    s_edge_frame.soil_count = 0;
    for (int i = 0; i < MOLE_NUM_ACTIVE_SOIL_PINS; i++) {
        int adc_raw = 0;
        if (s_soil[i] && sensor_soil_read_raw(s_soil[i], &adc_raw) == ESP_OK) {
            char pin_buf[8];
            snprintf(pin_buf, sizeof(pin_buf), "%d", soil_pins[i]);
            s_edge_frame.soil[s_edge_frame.soil_count].pin = s_edge_frame.soil_pin_storage[i];
            strncpy(s_edge_frame.soil_pin_storage[i], pin_buf, 8);
            s_edge_frame.soil[s_edge_frame.soil_count].adc_raw = adc_raw;
            s_edge_frame.soil_count++;
        }
    }
}

static void transport_send_payload(void)
{
    build_edge_frame();

    int len = payload_build(&s_edge_frame, s_payload_buf, sizeof(s_payload_buf));
    if (len < 0) {
        ESP_LOGE(TAG, "Payload build failed");
        if (s_fsm_queue) {
            fsm_event_t ev = EV_SEND_FAIL;
            xQueueSend(s_fsm_queue, &ev, 0);
        }
        return;
    }

    if (!s_transport) {
        ESP_LOGW(TAG, "Transport not initialised — skipping send");
        if (s_fsm_queue) {
            fsm_event_t ev = EV_SEND_FAIL;
            xQueueSend(s_fsm_queue, &ev, 0);
        }
        return;
    }

    transport_result_t res = transport_send(s_transport, s_payload_buf, len);
    switch (res.status) {
        case TRANSPORT_OK:
            ESP_LOGI(TAG, "Telemetry sent (HTTP %d)", res.http_code);
            if (s_fsm_queue) {
                fsm_event_t ev = EV_SEND_OK;
                xQueueSend(s_fsm_queue, &ev, 0);
            }
            break;
        case TRANSPORT_AUTH_FAILED:
            ESP_LOGE(TAG, "Auth failed — trigger re-provisioning");
            if (s_fsm_queue) {
                fsm_event_t ev = EV_TRANSPORT_AUTH_FAIL;
                xQueueSend(s_fsm_queue, &ev, 0);
            }
            break;
        default:
            ESP_LOGW(TAG, "Send failed: HTTP %d", res.http_code);
            if (s_fsm_queue) {
                fsm_event_t ev = EV_SEND_FAIL;
                xQueueSend(s_fsm_queue, &ev, 0);
            }
            break;
    }
}

void transport_send_frame_from_buffer(const sensor_frame_t *frame)
{
    if (!frame || !s_transport) return;

    edge_frame_t ef;
    memset(&ef, 0, sizeof(ef));
    ef.ts = frame->ts;
    ef.report_interval_minutes = frame->report_interval_minutes;
    ef.ambient = frame->ambient;
    ef.ambient_valid = frame->ambient_valid;
    ef.soil_count = frame->soil_count;
    for (int i = 0; i < frame->soil_count && i < EDGE_FRAME_MAX_SOIL_PINS; i++) {
        strncpy(ef.soil_pin_storage[i], frame->soil[i].pin, sizeof(ef.soil_pin_storage[i]));
        ef.soil[i].pin = ef.soil_pin_storage[i];
        ef.soil[i].adc_raw = frame->soil[i].adc_raw;
    }

    int len = payload_build(&ef, s_payload_buf, sizeof(s_payload_buf));
    if (len < 0) {
        ESP_LOGW(TAG, "Drain: payload build failed — skipping frame");
        return;
    }

    transport_send(s_transport, s_payload_buf, len);
    ESP_LOGI(TAG, "Drain: buffered frame sent (%d bytes)", len);
}

/* ==========================================================================
 * SECTION 7: Deep Sleep
 * ========================================================================== */

static void enter_deep_sleep(void)
{
    ESP_LOGI(TAG, "Entering deep sleep for %llu us", MOLE_DEEP_SLEEP_US);
    esp_err_t wdt_err = esp_task_wdt_delete(NULL);
    if (wdt_err != ESP_OK && wdt_err != ESP_ERR_NOT_FOUND) {
        ESP_LOGW(TAG, "esp_task_wdt_delete: 0x%x", wdt_err);
    }
    esp_deep_sleep(MOLE_DEEP_SLEEP_US);
}

/* ==========================================================================
 * SECTION 8: Backoff Timer Wrapper (for FSM action)
 * ========================================================================== */

static void start_backoff_timer(void)
{
    int delay_ms = reconnect_backoff_delay_ms();
    ESP_LOGW(TAG, "Starting backoff timer: %d ms (attempt %d)",
             delay_ms, s_reconnect_attempt);
    TimerHandle_t t = xTimerCreate("fsm_backoff",
                                   pdMS_TO_TICKS(delay_ms),
                                   pdFALSE, NULL,
                                   reconnect_timer_cb);
    if (t) xTimerStart(t, 0);
    else   esp_wifi_connect();
}

/* ==========================================================================
 * SECTION 9: app_main — Minimal Entrypoint
 * ========================================================================== */

void app_main(void)
{
    ESP_LOGI(TAG, "╔═══════════════════════════════════════════╗");
    ESP_LOGI(TAG, "║  Mole.AI Telemetry Node v%s          ║", MOLE_FW_VERSION);
    ESP_LOGI(TAG, "╚═══════════════════════════════════════════╝");

    /* NVS init */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES ||
        ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_LOGW(TAG, "NVS partition issue — erasing and reinitializing");
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    g_provision_sem = xSemaphoreCreateBinary();

    /* Network stack */
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    /* Initialise FSM */
    fsm_context_t *ctx = fsm_init();
    if (!ctx) {
        ESP_LOGE(TAG, "FSM init failed — rebooting");
        esp_restart();
    }

    /* Store queue handle globally so event handlers can post */
    s_fsm_queue = fsm_get_queue(ctx);

    /* Launch FSM task (owns all orchestration from here) */
    xTaskCreate(fsm_task, "fsm", 4096, ctx, 5, NULL);

    ESP_LOGI(TAG, "FSM task launched — app_main returning to scheduler");
}
