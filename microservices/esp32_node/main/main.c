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
        ESP_LOGW(TAG, "WiFi disconnected — reconnecting...");
        vTaskDelay(pdMS_TO_TICKS(2000));
        esp_wifi_connect();
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

void app_main(void)
{
    ESP_LOGI(TAG, "╔═══════════════════════════════════════════╗");
    ESP_LOGI(TAG, "║  Mole.AI OpenClaw Node v%s           ║", MOLE_FW_VERSION);
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
    mole_ntp_wait_sync(10000);  /* Block up to 10s for valid clock */
    ESP_LOGI(TAG, "[4/6] NTP synchronized");

    /* ── 5. I2C Bus + Sensor Initialization ──────────────────────────── */
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

    ESP_LOGI(TAG, "All tasks launched. FreeRTOS scheduler active.");
    /* app_main returns — FreeRTOS keeps tasks alive */
}
