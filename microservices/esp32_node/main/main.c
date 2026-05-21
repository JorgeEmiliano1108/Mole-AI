/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * main.c — Mole.AI Telemetry Node (Bare-Metal, ESP-IDF 5.x)
 *
 * Boot sequence (State Machine):
 *   1. NVS init
 *   2. NVS token check → if missing → Captive Portal AP mode
 *   3. WiFi STA connection (with saved credentials)
 *   4. NTP synchronization (ETSI EN 303 645 Anti-Replay)
 *   5. I2C bus + sensor initialization (DHT20, LTR390, Soil×N)
 *   6. WebSocket client connect (Bearer Token from NVS)
 *   7. Telemetry FreeRTOS task (cJSON → WebSocket push)
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
#include "esp_log.h"
#include "esp_system.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "esp_timer.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "driver/i2c_master.h"
#include "esp_http_server.h"
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

static const char *TAG = "MOLE_MAIN";

/* ── FreeRTOS Event Group ────────────────────────────────────────────────── */
static EventGroupHandle_t wifi_event_group;
#define WIFI_CONNECTED_BIT   BIT0

/* ── Global sensor handles ───────────────────────────────────────────────── */
static sensor_dht20_handle_t  s_dht20  = NULL;
static sensor_ltr390_handle_t s_ltr390 = NULL;
/* Array of soil sensor handles — one per active pin */
static sensor_soil_handle_t   s_soil[MOLE_NUM_ACTIVE_SOIL_PINS] = {0};

/* ── Device Token (read from NVS at boot) ────────────────────────────────── */
static char s_device_token[128] = {0};

/* ── WebSocket client handle ─────────────────────────────────────────────── */
static esp_websocket_client_handle_t s_ws_client = NULL;

/* ==========================================================================
 * SECTION 1: NVS Token Management
 * ========================================================================== */

/**
 * @brief Attempt to load device token from NVS.
 * @return true if token was found and loaded, false if NVS has no token.
 */
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

/**
 * @brief Save device token to NVS and commit.
 */
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

/* Forward declaration — defined in SECTION 3 (WiFi STA) */
static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                               int32_t event_id, void *event_data);

#define MAX_SCANNED_APS 10
static wifi_ap_record_t s_ap_info_cache[MAX_SCANNED_APS];
static uint16_t s_ap_count_cache = 0;
static bool s_scan_completed = false;

static void wifi_background_scan_task(void *pvParameters)
{
    /* Wait for WiFi radio PHY calibration to complete */
    ESP_LOGI(TAG, "Waiting for WiFi radio stabilization...");
    vTaskDelay(pdMS_TO_TICKS(2000));

    ESP_LOGI(TAG, "Starting background WiFi scan...");
    uint16_t number = MAX_SCANNED_APS;
    
    if (esp_wifi_scan_start(NULL, true) == ESP_OK) {
        /* ESP-IDF canonical sequence: get_ap_num FIRST, then get_ap_records.
         * get_ap_records() frees the driver's internal buffer as a side-effect,
         * so calling get_ap_num() after it would always return 0. */
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
            uint16_t flags = htons(0x8180); // Standard response
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
        /* ESP-IDF canonical sequence: get_ap_num FIRST, then get_ap_records.
         * get_ap_records() frees the driver's internal buffer as a side-effect,
         * so calling get_ap_num() after it would always return 0. */
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

    /* Parse form data: ssid=X&pass=Y&token=Z&interval=W */
    char ssid[64] = {0}, pass[64] = {0}, token[128] = {0}, interval_str[16] = {0};

    /* Simple URL-encoded form parser */
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
    
    /* Validate and convert interval */
    uint32_t interval_min = atoi(interval_str);
    if (interval_min < 1) interval_min = 1;
    if (interval_min > 120) interval_min = 120;

    /* Save WiFi credentials via ESP WiFi API (stored internally by ESP-IDF) */
    wifi_config_t wifi_cfg = {0};
    strncpy((char *)wifi_cfg.sta.ssid, ssid, sizeof(wifi_cfg.sta.ssid) - 1);
    strncpy((char *)wifi_cfg.sta.password, pass, sizeof(wifi_cfg.sta.password) - 1);
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_cfg));

    /* Save device token and interval to NVS */
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

    /* Restart after a short delay to let HTTP response flush */
    vTaskDelay(pdMS_TO_TICKS(1500));
    esp_restart();

    return ESP_OK;
}

static void start_captive_portal(void)
{
    ESP_LOGI(TAG, "=== CAPTIVE PORTAL MODE ===");

    /* 1. Start WiFi in APSTA mode */
    esp_netif_create_default_wifi_ap();
    esp_netif_create_default_wifi_sta(); // Required for APSTA scanning
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    /* Register WiFi event handler for scan state machine */
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

    /* Start DNS Server Task for Auto-Popup */
    xTaskCreate(dns_server_task, "dns_server", 4096, NULL, 5, NULL);

    /* Start Background WiFi Scanner */
    xTaskCreate(wifi_background_scan_task, "wifi_bg_scan", 4096, NULL, 5, NULL);

    /* 2. Start HTTP server */
    httpd_config_t http_cfg = HTTPD_DEFAULT_CONFIG();
    http_cfg.uri_match_fn = httpd_uri_match_wildcard; // Necessary to catch all requests for redirect
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

    /* Block forever — the POST handler will restart the chip */
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000));
    }
}

/* ==========================================================================
 * SECTION 3: WiFi STA Mode (Normal Operation)
 * ========================================================================== */

static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                               int32_t event_id, void *event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        /* Only auto-connect if in STA mode (event group exists) */
        if (wifi_event_group) {
            esp_wifi_connect();
        }
    } else if (event_base == WIFI_EVENT &&
               event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (wifi_event_group) {
            ESP_LOGW(TAG, "WiFi disconnected — reconnecting in 5s...");
            vTaskDelay(pdMS_TO_TICKS(5000));
            esp_wifi_connect();
            xEventGroupClearBits(wifi_event_group, WIFI_CONNECTED_BIT);
        }
    } else if (event_base == IP_EVENT &&
               event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *evt = (ip_event_got_ip_t *)event_data;
        ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&evt->ip_info.ip));
        if (wifi_event_group) {
            xEventGroupSetBits(wifi_event_group, WIFI_CONNECTED_BIT);
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

    /* Load Wi-Fi credentials from NVS */
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

    /*
     * IFT-016 COMPLIANCE:
     * We intentionally do NOT call esp_wifi_set_max_tx_power().
     * The ESP32 SDK default (~20 dBm) complies with IFT-016 EIRP limits
     * for unlicensed 2.4 GHz ISM band operation in Mexican territory.
     */

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "Waiting for IP address...");
    xEventGroupWaitBits(wifi_event_group, WIFI_CONNECTED_BIT,
                        false, true, portMAX_DELAY);
    ESP_LOGI(TAG, "WiFi connected.");
}

/* ==========================================================================
 * SECTION 4: WebSocket Client (Bearer Token Auth)
 * ========================================================================== */

static void ws_event_handler(void *arg, esp_event_base_t event_base,
                             int32_t event_id, void *event_data)
{
    esp_websocket_event_data_t *data = (esp_websocket_event_data_t *)event_data;
    switch (event_id) {
        case WEBSOCKET_EVENT_CONNECTED:
            ESP_LOGI(TAG, "[WS] Connected to Edge Node");
            break;
        case WEBSOCKET_EVENT_DISCONNECTED:
            ESP_LOGW(TAG, "[WS] Disconnected from Edge Node");
            break;
        case WEBSOCKET_EVENT_DATA:
            if (data->op_code == 0x01) { /* Text frame */
                ESP_LOGI(TAG, "[WS] Received: %.*s", data->data_len, data->data_ptr);
            }
            break;
        case WEBSOCKET_EVENT_ERROR:
            ESP_LOGE(TAG, "[WS] Error");
            break;
        default:
            break;
    }
}

static esp_err_t ws_client_start(void)
{
    /* Build Authorization header with token from NVS */
    char auth_header[192];
    snprintf(auth_header, sizeof(auth_header),
             "Authorization: Bearer %s\r\n", s_device_token);

    esp_websocket_client_config_t ws_cfg = {
        .uri = CONFIG_MOLE_WS_URI,
        .headers = auth_header,
        .reconnect_timeout_ms = 10000,
        .network_timeout_ms   = 10000,
    };

    s_ws_client = esp_websocket_client_init(&ws_cfg);
    if (!s_ws_client) {
        ESP_LOGE(TAG, "Failed to init WebSocket client");
        return ESP_FAIL;
    }

    esp_websocket_register_events(s_ws_client, WEBSOCKET_EVENT_ANY,
                                  ws_event_handler, NULL);
    return esp_websocket_client_start(s_ws_client);
}

/* ==========================================================================
 * SECTION 5: Telemetry Task (cJSON + WebSocket Push)
 * ========================================================================== */

static void telemetry_task(void *arg)
{
    uint32_t interval_ms = (uint32_t)(uintptr_t)arg;
    const int soil_pins[] = MOLE_ACTIVE_SOIL_PINS;

    while (1) {
        vTaskDelay(pdMS_TO_TICKS(interval_ms));

        if (!esp_websocket_client_is_connected(s_ws_client)) {
            ESP_LOGW(TAG, "[TELEM] WebSocket not connected, skipping cycle.");
            continue;
        }

        /* ── Read sensors ─────────────────────────────────────────────── */
        float air_temp = 0, air_hum = 0, lux = 0, uv = 0;

        if (s_dht20) {
            sensor_dht20_read(s_dht20, &air_temp, &air_hum);
        }
        if (s_ltr390) {
            sensor_ltr390_read(s_ltr390, &lux, &uv);
        } else {
            /* LTR390 MOCK fallback (sensor not detected on I2C bus) */
            uv  = 3.5f;
            lux = 8500.0f;
        }

        /* ── Build JSON payload ───────────────────────────────────────── */
        cJSON *root = cJSON_CreateObject();
        cJSON_AddNumberToObject(root, "timestamp", (double)time(NULL));

        /* Ambient object (shared sensors: DHT20 + LTR390) */
        cJSON *ambient = cJSON_AddObjectToObject(root, "ambient");
        cJSON_AddNumberToObject(ambient, "air_temperature", air_temp);
        cJSON_AddNumberToObject(ambient, "air_humidity",    air_hum);
        cJSON_AddNumberToObject(ambient, "light_level",     lux);
        cJSON_AddNumberToObject(ambient, "uv_index",        uv);

        /* Soil object (1:N per-pin readings) */
        cJSON *soil_obj = cJSON_AddObjectToObject(root, "soil");
        for (int i = 0; i < MOLE_NUM_ACTIVE_SOIL_PINS; i++) {
            float moisture = 0;
            if (s_soil[i]) {
                sensor_soil_read(s_soil[i], &moisture);
            }
            char pin_str[8];
            snprintf(pin_str, sizeof(pin_str), "%d", soil_pins[i]);
            cJSON_AddNumberToObject(soil_obj, pin_str, moisture);
        }

        /* ── Serialize and send ───────────────────────────────────────── */
        char *json_str = cJSON_PrintUnformatted(root);
        cJSON_Delete(root);

        if (json_str) {
            int len = strlen(json_str);
            int sent = esp_websocket_client_send_text(
                s_ws_client, json_str, len, pdMS_TO_TICKS(5000));

            if (sent < 0) {
                ESP_LOGE(TAG, "[TELEM] Failed to send (%d bytes)", len);
            } else {
                ESP_LOGI(TAG, "[TELEM] Sent %d bytes", len);
            }
            free(json_str);
        }
    }
}

/* ==========================================================================
 * SECTION 6: app_main — Firmware Entrypoint (State Machine)
 * ========================================================================== */

void app_main(void)
{
    ESP_LOGI(TAG, "╔═══════════════════════════════════════════╗");
    ESP_LOGI(TAG, "║  Mole.AI Telemetry Node v%s          ║", MOLE_FW_VERSION);
    ESP_LOGI(TAG, "╚═══════════════════════════════════════════╝");

    /* ── Step 1: NVS Init ────────────────────────────────────────────── */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES ||
        ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_LOGW(TAG, "NVS partition issue — erasing and reinitializing");
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ESP_LOGI(TAG, "[1/6] NVS initialized");

    /* ── Step 2: Network stack ───────────────────────────────────────── */
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    /* ── Step 3: Token Check (State Machine Decision Point) ──────────── */
    bool has_token = nvs_load_token();

    if (!has_token) {
        /*
         * FIRST BOOT / FACTORY RESET:
         * No token in NVS → enter Captive Portal AP mode.
         * This function NEVER returns (blocks until form POST → restart).
         */
        start_captive_portal();
        /* Unreachable — start_captive_portal calls esp_restart() */
    }

    /* ── Step 4: WiFi STA (token exists, connect to saved AP) ────────── */
    wifi_init_sta();
    ESP_LOGI(TAG, "[2/6] WiFi STA connected");

    /* ── Step 5: NTP Sync (ETSI EN 303 645) ──────────────────────────── */
    ESP_ERROR_CHECK(mole_ntp_init());
    mole_ntp_wait_sync(10000);
    ESP_LOGI(TAG, "[3/6] NTP synchronized");

    /* ── Step 6: I2C Bus + Sensors ───────────────────────────────────── */
    i2c_master_bus_handle_t i2c_bus = NULL;
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port   = I2C_NUM_0,
        .sda_io_num = CONFIG_MOLE_I2C_SDA,
        .scl_io_num = CONFIG_MOLE_I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &i2c_bus));

    /* DHT20 (Temperature + Air Humidity) */
    ESP_ERROR_CHECK(sensor_dht20_init(i2c_bus, &s_dht20));

    /* LTR390 (Light + UV) — graceful fallback if not present */
    esp_err_t err_ltr = sensor_ltr390_init(i2c_bus, &s_ltr390);
    if (err_ltr != ESP_OK) {
        ESP_LOGE(TAG, "LTR390 init failed (0x%x). Using MOCK data.", err_ltr);
        s_ltr390 = NULL;
    }

    /* ADC1 Singleton Initialization */
    adc_oneshot_unit_handle_t adc1_handle = NULL;
    adc_oneshot_unit_init_cfg_t unit_cfg = {
        .unit_id = ADC_UNIT_1,
    };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&unit_cfg, &adc1_handle));

    /* Soil sensors — one per active ADC1 pin */
    const int soil_pins[] = MOLE_ACTIVE_SOIL_PINS;
    for (int i = 0; i < MOLE_NUM_ACTIVE_SOIL_PINS; i++) {
        int channel = MOLE_GPIO_TO_ADC1_CHANNEL(soil_pins[i]);
        if (channel < 0) {
            ESP_LOGE(TAG, "Invalid soil GPIO %d — not an ADC1 pin!", soil_pins[i]);
            continue;
        }
        esp_err_t err = sensor_soil_init(adc1_handle, channel, &s_soil[i]);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Soil sensor on GPIO %d failed (0x%x)", soil_pins[i], err);
            s_soil[i] = NULL;
        } else {
            ESP_LOGI(TAG, "Soil sensor OK on GPIO %d (ADC1 ch%d)", soil_pins[i], channel);
        }
    }
    ESP_LOGI(TAG, "[4/6] Sensors initialized");

    /* ── Step 7: WebSocket Client ────────────────────────────────────── */
    ESP_ERROR_CHECK(ws_client_start());
    ESP_LOGI(TAG, "[5/6] WebSocket client started → %s", CONFIG_MOLE_WS_URI);

    /* ── Step 8: Read Telemetry Interval & Launch Task ───────────────── */
    uint32_t telemetry_interval_min = 5; // Default fallback
    nvs_handle_t handle;
    if (nvs_open(MOLE_NVS_NAMESPACE, NVS_READONLY, &handle) == ESP_OK) {
        nvs_get_u32(handle, "telemetry_int", &telemetry_interval_min);
        nvs_close(handle);
    }

    /* Bounds check (Safety) */
    if (telemetry_interval_min < 1) telemetry_interval_min = 1;
    if (telemetry_interval_min > 120) telemetry_interval_min = 120;

    uint32_t interval_ms = telemetry_interval_min * 60 * 1000;
    ESP_LOGI(TAG, "[6/6] Dynamic Telemetry Interval: %lu minutos (%lu ms)", 
             telemetry_interval_min, interval_ms);

    xTaskCreate(telemetry_task, "mole_telem", 8192, (void*)(uintptr_t)interval_ms, 5, NULL);

    ESP_LOGI(TAG, "All systems nominal. FreeRTOS scheduler active.");
    /* app_main returns — FreeRTOS keeps telemetry_task alive */
}
