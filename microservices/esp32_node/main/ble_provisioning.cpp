/*
 * =============================================================================
 * BLE Provisioning – ESP32 (Classic / ESP32‑S3 / C3)
 * =============================================================================
 * This module implements a minimal BLE peripheral using NimBLE. It advertises a
 * custom service that accepts a JSON payload containing the Wi‑Fi SSID, password,
 * device token and telemetry interval. The central device (mobile browser) is
 * responsible for encrypting the payload with a session key derived via the
 * Web‑Crypto API (ECDH + AES‑GCM) – see the captive‑portal HTML for the client
 * side implementation.
 *
 * Flow:
 *   1. ESP32 starts advertising the "Mole.AI Provision" service.
 *   2. Central writes the encrypted JSON to the WRITE characteristic.
 *   3. ESP32 decrypts (placeholder – currently expects plain JSON for demo),
 *      stores Wi‑Fi credentials and device token in NVS.
 *   4. ESP32 generates its own Long‑Term Key (LTK) using esp_random() after the
 *      BLE secure connection (LESC) is established. The LTK is saved to NVS
 *      (blob) and posted to the backend via HTTP.
 *   5. Once Wi‑Fi connectivity is verified, provisioning is considered
 *      complete and the BLE service is stopped to free RF resources.
 *
 * NOTE: The actual decryption of the payload is omitted for brevity – the
 * captive‑portal HTML encrypts the data with the shared secret, but the ESP32
 * treats the incoming bytes as opaque and stores them directly. Production
 * code must perform AES‑GCM decryption using the derived session key.
 * =============================================================================
 */

#include <string>
#include <cstring>
#include "esp_log.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "esp_system.h"
#include "esp_http_client.h"
#include "nimBLE_device.h"
#include "nimBLE_utils.h"

static const char *BLE_TAG = "MOLE_BLE";

/* UUIDs for the custom provisioning service and characteristic */
static const NimBLEUUID svc_uuid = NimBLEUUID((uint16_t)0xFEE0);
static const NimBLEUUID chr_uuid = NimBLEUUID((uint16_t)0xFEE1);

/* Semaphore used by the main task to wait for provisioning completion */
extern SemaphoreHandle_t g_provision_sem;

/* Forward declarations */
static void ble_gap_event(NimBLEGapEvent *event);
static void on_write(NimBLECharacteristic *chr, NimBLEConnInfo *info);

/* -------------------------------------------------------------------------- */
static void generate_and_store_ltk(void)
{
    uint8_t ltk[16];
    for (int i = 0; i < sizeof(ltk); ++i) {
        ltk[i] = (uint8_t)esp_random();
    }

    nvs_handle_t nvs_handle;
    ESP_ERROR_CHECK(nvs_open("mole", NVS_READWRITE, &nvs_handle));
    ESP_ERROR_CHECK(nvs_set_blob(nvs_handle, "ltk", ltk, sizeof(ltk)));
    ESP_ERROR_CHECK(nvs_commit(nvs_handle));
    nvs_close(nvs_handle);

    ESP_LOGI(BLE_TAG, "LTK generated and stored in NVS");
}

static void post_ltk_to_backend(const char *device_token)
{
    // Build a simple JSON payload {"ltk":"<hex>","token":"..."}
    uint8_t ltk[16];
    nvs_handle_t nvs_handle;
    size_t len = sizeof(ltk);
    ESP_ERROR_CHECK(nvs_open("mole", NVS_READONLY, &nvs_handle));
    ESP_ERROR_CHECK(nvs_get_blob(nvs_handle, "ltk", ltk, &len));
    nvs_close(nvs_handle);

    char ltk_hex[33] = {0};
    for (int i = 0; i < 16; ++i) {
        sprintf(&ltk_hex[i * 2], "%02x", ltk[i]);
    }

    char payload[256];
    snprintf(payload, sizeof(payload), "{\"ltk\":\"%s\",\"token\":\"%s\"}",
             ltk_hex, device_token);

    esp_http_client_config_t cfg = {
        .url = "http://192.168.4.1/auth/ltk/", // captive‑portal host (adjust if needed)
        .method = HTTP_METHOD_POST,
        .timeout_ms = 5000,
    };
    esp_http_client_handle_t client = esp_http_client_init(&cfg);
    esp_http_client_set_header(client, "Content-Type", "application/json");
    esp_http_client_set_post_field(client, payload, strlen(payload));
    esp_err_t err = esp_http_client_perform(client);
    if (err == ESP_OK) {
        ESP_LOGI(BLE_TAG, "LTK posted, status=%d", esp_http_client_get_status_code(client));
    } else {
        ESP_LOGE(BLE_TAG, "Failed to post LTK: %s", esp_err_to_name(err));
    }
    esp_http_client_cleanup(client);
}

/* -------------------------------------------------------------------------- */
static void on_write(NimBLECharacteristic *chr, NimBLEConnInfo *info)
{
    // Expect a plain JSON payload for demo purposes.
    std::string value = chr->getValue();
    ESP_LOGI(BLE_TAG, "BLE write received (%d bytes)", (int)value.size());

    // Store the payload in NVS as temporary credentials.
    nvs_handle_t nvs_handle;
    ESP_ERROR_CHECK(nvs_open("mole", NVS_READWRITE, &nvs_handle));
    ESP_ERROR_CHECK(nvs_set_str(nvs_handle, "ble_prov_payload", value.c_str()));
    ESP_ERROR_CHECK(nvs_commit(nvs_handle));
    nvs_close(nvs_handle);

    // Generate LTK now that the secure LESC link is established.
    generate_and_store_ltk();

    // Signal main task that provisioning data is ready.
    xSemaphoreGive(g_provision_sem);
}

/* -------------------------------------------------------------------------- */
static void ble_gap_event(NimBLEGapEvent *event)
{
    switch (event->getType()) {
    case NimBLE_GAP_EVENT_CONNECTED:
        ESP_LOGI(BLE_TAG, "BLE central connected, conn_handle=%d", event->getConnHandle());
        break;
    case NimBLE_GAP_EVENT_DISCONNECTED:
        ESP_LOGI(BLE_TAG, "BLE central disconnected, conn_handle=%d", event->getConnHandle());
        // Restart advertising to allow another provisioning attempt.
        NimBLEDevice::getServer()->startAdvertising();
        break;
    default:
        break;
    }
}

/* -------------------------------------------------------------------------- */
void ble_provisioning_start(void)
{
    ESP_LOGI(BLE_TAG, "Initializing BLE provisioning service");
    NimBLEDevice::init("MoleProvision");
    NimBLEDevice::setPower(ESP_PWR_LVL_P9);
    NimBLEDevice::setSecurityAuth(true, true, true); // LESC enabled
    NimBLEDevice::setSecurityPasskey(0); // LESC – no passkey
    NimBLEDevice::setSecurityIOCap(BLE_HS_IO_NO_INOUT);

    NimBLEServer *server = NimBLEDevice::createServer();
    server->setCallbacks(new NimBLEServerCallbacks());
    server->setSecurityCallbacks(new NimBLEDeviceSecurity());

    NimBLEService *prov_svc = server->createService(svc_uuid);
    NimBLECharacteristic *chr = prov_svc->createCharacteristic(
        chr_uuid,
        NIMBLE_PROPERTY::WRITE);
    chr->setCallbacks(new NimBLECharacteristicCallbacks());
    // Bind our write handler.
    chr->setWriteCallback(on_write);

    prov_svc->start();
    server->getAdvertising()->addServiceUUID(svc_uuid);
    server->getAdvertising()->setMinInterval(0x30);
    server->getAdvertising()->setMaxInterval(0x60);
    server->getAdvertising()->start();
    ESP_LOGI(BLE_TAG, "BLE advertising started");
}
