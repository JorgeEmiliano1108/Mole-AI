/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * main.c — Mole.AI OpenClaw Bare-Metal Agent Entrypoint
 *
 * Boot sequence:
 *   1. NVS (encrypted)
 *   2. Network stack + WiFi STA
 *   3. Ed25519 identity (generate on first boot / load on subsequent)
 *   4. NTP synchronization (ETSI EN 303 645 Anti-Replay)
 *   5. I2C bus + sensor initialization
 *   6. OpenClaw agent lifecycle (capabilities + connect + telemetry task)
 *
 * Regulatory Compliance:
 *   IFT-016:       No calls to esp_wifi_set_max_tx_power()
 *   ETSI EN 303645: mole_ntp_wait_sync() blocks until clock is valid
 *   LFPDPPP:       Zero PII in flash — identity = Ed25519 public key
 * =============================================================================
 */

#include <stdio.h>
#include <string.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "esp_timer.h"
#include "esp_sleep.h"
#include "nvs_flash.h"
#include "driver/i2c_master.h"

/* Mole.AI components */
#include "mole_config.h"
#include "mole_identity.h"
#include "mole_ntp.h"
#include "mole_openclaw.h"
#include "sensor_dht20.h"
#include "sensor_ltr390.h"
#include "sensor_soil.h"

static const char *TAG = "MOLE_MAIN";

#include "wifi_provisioning/manager.h"
#include "wifi_provisioning/scheme_ble.h"

/* ── FreeRTOS Event Group for WiFi/Prov ──────────────────────────────────── */
static EventGroupHandle_t wifi_event_group;
const int WIFI_CONNECTED_EVENT = BIT0;
const int WIFI_PROV_DONE_EVENT = BIT1;

/* ── WiFi Asynchronous Reconnection Timer ────────────────────────────────── */
static esp_timer_handle_t wifi_reconnect_timer;

static void wifi_reconnect_cb(void* arg)
{
    ESP_LOGI(TAG, "Reconectando WiFi...");
    esp_wifi_connect();
}

static void init_wifi_reconnect_timer(void)
{
    esp_timer_create_args_t reconnect_timer_args = {
        .callback = &wifi_reconnect_cb,
        .name = "wifi_reconnect"
    };
    ESP_ERROR_CHECK(esp_timer_create(&reconnect_timer_args, &wifi_reconnect_timer));
}

/* ── WiFi STA Event Handler ──────────────────────────────────────────────── */

static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                               int32_t event_id, void *event_data)
{
    if (event_base == WIFI_PROV_EVENT) {
        switch (event_id) {
            case WIFI_PROV_START:
                ESP_LOGI(TAG, "Provisioning started. Connect to Bluetooth.");
                break;
            case WIFI_PROV_CRED_RECV:
                ESP_LOGI(TAG, "Received WiFi credentials.");
                break;
            case WIFI_PROV_CRED_FAIL:
                ESP_LOGE(TAG, "Provisioning failed! Reason: Authentication Failed.");
                wifi_prov_mgr_reset_sm_state_on_failure();
                break;
            case WIFI_PROV_CRED_SUCCESS:
                ESP_LOGI(TAG, "Provisioning successful.");
                break;
            case WIFI_PROV_END:
                ESP_LOGI(TAG, "Provisioning end. Manager deinit.");
                wifi_prov_mgr_deinit();
                xEventGroupSetBits(wifi_event_group, WIFI_PROV_DONE_EVENT);
                break;
            default:
                break;
        }
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT &&
               event_id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGW(TAG, "WiFi desconectado — programando reconexión en 5s...");
        esp_timer_start_once(wifi_reconnect_timer, 5000000);
        xEventGroupClearBits(wifi_event_group, WIFI_CONNECTED_EVENT);
    } else if (event_base == IP_EVENT &&
               event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *evt = (ip_event_got_ip_t *)event_data;
        ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&evt->ip_info.ip));
        xEventGroupSetBits(wifi_event_group, WIFI_CONNECTED_EVENT);
    }
}

static void wifi_init_sta(void)
{
    init_wifi_reconnect_timer();
    wifi_event_group = xEventGroupCreate();

    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_PROV_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL));

    /*
     * IFT-016 COMPLIANCE:
     * We intentionally do NOT call esp_wifi_set_max_tx_power().
     * The ESP32 SDK default (~20 dBm) complies with IFT-016 EIRP limits
     * for unlicensed 2.4 GHz ISM band operation in Mexican territory.
     */

    wifi_prov_mgr_config_t config = {
        .scheme = wifi_prov_scheme_ble,
        .scheme_event_handler = WIFI_PROV_EVENT_HANDLER_NONE
    };
    ESP_ERROR_CHECK(wifi_prov_mgr_init(config));

    bool provisioned = false;
    ESP_ERROR_CHECK(wifi_prov_mgr_is_provisioned(&provisioned));

    if (!provisioned) {
        ESP_LOGI(TAG, "Starting BLE Provisioning...");
        /* Create standard ESP BLE prov service */
        ESP_ERROR_CHECK(wifi_prov_mgr_start_provisioning(WIFI_PROV_SECURITY_0, NULL, "Mole_OpenClaw_Node", NULL));
        
        ESP_LOGI(TAG, "Blocking until provisioning completes...");
        xEventGroupWaitBits(wifi_event_group, WIFI_PROV_DONE_EVENT, false, true, portMAX_DELAY);
    } else {
        ESP_LOGI(TAG, "Already provisioned. Connecting to saved AP...");
        wifi_prov_mgr_deinit();
        ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
        ESP_ERROR_CHECK(esp_wifi_start());
    }

    ESP_LOGI(TAG, "Waiting for IP address...");
    xEventGroupWaitBits(wifi_event_group, WIFI_CONNECTED_EVENT, false, true, portMAX_DELAY);
    ESP_LOGI(TAG, "WiFi connected securely.");
}

/* ── app_main — Firmware Entrypoint ──────────────────────────────────────── */

/* ── Deep Sleep Survival Function ────────────────────────────────────────── */
static void enter_deep_sleep(void) {
    ESP_LOGI(TAG, "Preparando transición a Deep Sleep...");
    esp_err_t err = esp_wifi_stop();
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "Radio WiFi apagada correctamente.");
    } else {
        ESP_LOGW(TAG, "Fallo al apagar WiFi: %s", esp_err_to_name(err));
    }
    
    // MOLE_DEEP_SLEEP_US comes from mole_config.h
    esp_sleep_enable_timer_wakeup(MOLE_DEEP_SLEEP_US);
    
    ESP_LOGI(TAG, "Entrando en Deep Sleep. ¡Hasta luego!");
    esp_deep_sleep_start();
}

void app_main(void)
{
    ESP_LOGI(TAG, "╔═══════════════════════════════════════════╗");
    ESP_LOGI(TAG, "║  Mole.AI Node v%s           ║", MOLE_FW_VERSION);
    ESP_LOGI(TAG, "╚═══════════════════════════════════════════╝");

    /* ── 1. NVS (encrypted partition for Ed25519 keys) ───────────────── */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES ||
        ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_LOGW(TAG, "NVS partition issue — erasing and reinitializing");
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ESP_LOGI(TAG, "[1/6] NVS initialized (encrypted)");

    /* ── 2. Network stack + WiFi ─────────────────────────────────────── */
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    wifi_init_sta();
    ESP_LOGI(TAG, "[2/6] Network stack initialized");

    /* ── 3. Zero-Trust Identity (Ed25519 keypair in NVS) ─────────────── */
    mole_identity_handle_t identity = NULL;
    ESP_ERROR_CHECK(mole_identity_init(&identity));

    char pub_hex[65];
    mole_identity_get_public_key_hex(identity, pub_hex, sizeof(pub_hex));
    ESP_LOGI(TAG, "[3/6] Identity loaded — PubKey: %.16s...", pub_hex);
    /* LFPDPPP: No PII stored. Identity = Ed25519 public key fingerprint. */

    /* ── 4. NTP Sync (ETSI EN 303 645 — Anti-Replay) ────────────────── */
    ESP_ERROR_CHECK(mole_ntp_init());
    mole_ntp_wait_sync(10000);  /* Intento inicial de 10s */
    
    // Bloqueo estricto: No avanzar si el año es menor a 2026 (1900 + 126)
    time_t now;
    struct tm timeinfo;
    time(&now);
    localtime_r(&now, &timeinfo);
    
    while (timeinfo.tm_year < 126) {
        ESP_LOGW(TAG, "NTP no sincronizado (Año: %d). Bloqueando inicio de OpenClaw...", 1900 + timeinfo.tm_year);
        vTaskDelay(pdMS_TO_TICKS(5000)); // Espera asíncrona de 5s
        time(&now);
        localtime_r(&now, &timeinfo);
    }
    ESP_LOGI(TAG, "[4/6] NTP synchronized (Año verificado: %d)", 1900 + timeinfo.tm_year);
    /* [Fase 1] Escáner I2C Diagnóstico */
    ESP_LOGW(TAG, "=== INICIANDO ESCÁNER I2C ===");
    for (uint8_t addr = 1; addr < 128; addr++) {
        esp_err_t ret = i2c_master_probe(i2c_bus, addr, 100);
        if (ret == ESP_OK) {
            ESP_LOGW(TAG, "-> Dispositivo I2C responsivo en dirección: 0x%02X", addr);
        }
    }
    ESP_LOGW(TAG, "=============================");

    /* [Fase 2] Estabilización Power-On Reset */
    vTaskDelay(pdMS_TO_TICKS(100));

    sensor_dht20_handle_t  dht20  = NULL;
    sensor_ltr390_handle_t ltr390 = NULL;
    sensor_soil_handle_t   soil   = NULL;

    ESP_ERROR_CHECK(sensor_dht20_init(i2c_bus, &dht20));
    ESP_ERROR_CHECK(sensor_soil_init(CONFIG_MOLE_SOIL_ADC_CHANNEL, &soil));
    
    /* [Fase 3] LTR390 Fallback (Evitar abort) */
    esp_err_t err_ltr = sensor_ltr390_init(i2c_bus, &ltr390);
    if (err_ltr != ESP_OK) {
        ESP_LOGE(TAG, "[Fase 3] LTR390 Falló (0x%x). Activando datos MOCK.", err_ltr);
        ltr390 = NULL;
    }

    ESP_LOGI(TAG, "[5/6] Sensors: DHT20 + Soil initialized. LTR390 status: %s", ltr390 ? "OK" : "MOCK");

    /* ── 6. OpenClaw Agent (capabilities + connect + telemetry) ──────── */
    ESP_ERROR_CHECK(mole_openclaw_start(identity, dht20, ltr390, soil));
    ESP_LOGI(TAG, "[6/6] OpenClaw agent started");

    ESP_LOGI(TAG, "All tasks launched. Executing Deep Sleep transition.");
    enter_deep_sleep();
}
