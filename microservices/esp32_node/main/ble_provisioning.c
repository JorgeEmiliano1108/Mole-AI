/*
 * =============================================================================
 * BLE Provisioning – ESP32 (Native NimBLE in C)
 * =============================================================================
 * This module implements a minimal BLE peripheral using ESP-IDF native NimBLE.
 * It advertises a custom service that accepts a JSON payload containing Wi-Fi 
 * credentials and a device token.
 */

#include <string.h>
#include <stdio.h>
#include "esp_log.h"
#include "esp_random.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "esp_system.h"
#include "esp_http_client.h"

/* NimBLE Includes */
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "host/ble_hs.h"
#include "host/ble_uuid.h"
#include "host/ble_gap.h"
#include "host/ble_gatt.h"
#include "services/gap/ble_svc_gap.h"
#include "services/gatt/ble_svc_gatt.h"
#include "host/util/util.h"
#include "host/ble_store.h"

static const char *BLE_TAG = "MOLE_BLE";

/* Custom Service & Characteristic UUIDs */
/* Service: FEE0 */
static const ble_uuid16_t svc_uuid = BLE_UUID16_INIT(0xFEE0);
/* Characteristic: FEE1 */
static const ble_uuid16_t chr_uuid = BLE_UUID16_INIT(0xFEE1);

/* Semaphore used by the main task */
extern SemaphoreHandle_t g_provision_sem;

static uint8_t own_addr_type;

/* Forward declarations */
static int gap_event_cb(struct ble_gap_event *event, void *arg);
static int gatt_chr_access_cb(uint16_t conn_handle, uint16_t attr_handle,
                              struct ble_gatt_access_ctxt *ctxt, void *arg);

/* -------------------------------------------------------------------------- */
/* 1. GATT Service Definition */
/* -------------------------------------------------------------------------- */
static const struct ble_gatt_svc_def gatt_svcs[] = {
    {
        .type = BLE_GATT_SVC_TYPE_PRIMARY,
        .uuid = &svc_uuid.u,
        .characteristics = (struct ble_gatt_chr_def[]) {
            {
                .uuid = &chr_uuid.u,
                .access_cb = gatt_chr_access_cb,
                .flags = BLE_GATT_CHR_F_WRITE,
            },
            { 0 } /* No more characteristics in this service */
        },
    },
    { 0 } /* No more services */
};

/* -------------------------------------------------------------------------- */
/* Helper Functions for LTK */
/* -------------------------------------------------------------------------- */
static void generate_and_store_ltk(void)
{
    uint8_t ltk[16];
    for (int i = 0; i < sizeof(ltk); ++i) {
        ltk[i] = (uint8_t)(esp_random() & 0xFF);
    }

    nvs_handle_t nvs_handle;
    esp_err_t err = nvs_open("mole", NVS_READWRITE, &nvs_handle);
    if (err == ESP_OK) {
        nvs_set_blob(nvs_handle, "ltk", ltk, sizeof(ltk));
        nvs_commit(nvs_handle);
        nvs_close(nvs_handle);
        ESP_LOGI(BLE_TAG, "LTK generated and stored in NVS");
    } else {
        ESP_LOGE(BLE_TAG, "Failed to open NVS to store LTK");
    }
}

/* -------------------------------------------------------------------------- */
/* 2. GATT Access Callback (Write Handler) */
/* -------------------------------------------------------------------------- */
static int gatt_chr_access_cb(uint16_t conn_handle, uint16_t attr_handle,
                              struct ble_gatt_access_ctxt *ctxt, void *arg)
{
    if (ctxt->op == BLE_GATT_ACCESS_OP_WRITE_CHR) {
        uint16_t len = OS_MBUF_PKTLEN(ctxt->om);
        if (len > 0) {
            char *buf = malloc(len + 1);
            if (buf) {
                os_mbuf_copydata(ctxt->om, 0, len, buf);
                buf[len] = '\0';
                ESP_LOGI(BLE_TAG, "BLE write received (%d bytes)", len);

                // Store the payload in NVS
                nvs_handle_t nvs_handle;
                if (nvs_open("mole", NVS_READWRITE, &nvs_handle) == ESP_OK) {
                    nvs_set_str(nvs_handle, "ble_prov_payload", buf);
                    nvs_commit(nvs_handle);
                    nvs_close(nvs_handle);
                }

                free(buf);

                // Generate LTK and signal main task
                generate_and_store_ltk();
                if (g_provision_sem) {
                    xSemaphoreGive(g_provision_sem);
                }
            } else {
                ESP_LOGE(BLE_TAG, "Out of memory allocating payload buffer");
                return BLE_ATT_ERR_INSUFFICIENT_RES;
            }
        }
    }
    return 0;
}

/* -------------------------------------------------------------------------- */
/* 3. GAP Event Callback */
/* -------------------------------------------------------------------------- */
static void ble_app_advertise(void)
{
    struct ble_gap_adv_params adv_params;
    struct ble_hs_adv_fields fields;
    const char *name = ble_svc_gap_device_name();
    int rc;

    memset(&fields, 0, sizeof fields);
    fields.flags = BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP;
    fields.tx_pwr_lvl_is_present = 1;
    fields.tx_pwr_lvl = BLE_HS_ADV_TX_PWR_LVL_AUTO;

    fields.name = (uint8_t *)name;
    fields.name_len = strlen(name);
    fields.name_is_complete = 1;

    fields.uuids16 = (ble_uuid16_t[]){ svc_uuid };
    fields.num_uuids16 = 1;
    fields.uuids16_is_complete = 1;

    rc = ble_gap_adv_set_fields(&fields);
    if (rc != 0) {
        ESP_LOGE(BLE_TAG, "Error setting advertisement data; rc=%d", rc);
        return;
    }

    memset(&adv_params, 0, sizeof adv_params);
    adv_params.conn_mode = BLE_GAP_CONN_MODE_UND;
    adv_params.disc_mode = BLE_GAP_DISC_MODE_GEN;
    adv_params.itvl_min = 0x30;
    adv_params.itvl_max = 0x60;

    rc = ble_gap_adv_start(own_addr_type, NULL, BLE_HS_FOREVER,
                           &adv_params, gap_event_cb, NULL);
    if (rc != 0) {
        ESP_LOGE(BLE_TAG, "Error enabling advertising; rc=%d", rc);
        return;
    }
    ESP_LOGI(BLE_TAG, "BLE advertising started");
}

static int gap_event_cb(struct ble_gap_event *event, void *arg)
{
    switch (event->type) {
    case BLE_GAP_EVENT_CONNECT:
        ESP_LOGI(BLE_TAG, "BLE central connected, status=%d", event->connect.status);
        if (event->connect.status != 0) {
            ble_app_advertise();
        }
        break;

    case BLE_GAP_EVENT_DISCONNECT:
        ESP_LOGI(BLE_TAG, "BLE central disconnected, reason=%d", event->disconnect.reason);
        // Restart advertising
        ble_app_advertise();
        break;

    default:
        break;
    }
    return 0;
}

/* -------------------------------------------------------------------------- */
/* 4. NimBLE Host Task & Sync */
/* -------------------------------------------------------------------------- */
static void ble_app_on_sync(void)
{
    int rc = ble_hs_util_ensure_addr(0);
    if (rc != 0) {
        ESP_LOGE(BLE_TAG, "Error ensuring address");
        return;
    }
    rc = ble_hs_id_infer_auto(0, &own_addr_type);
    if (rc != 0) {
        ESP_LOGE(BLE_TAG, "Error determining address type");
        return;
    }

    ble_app_advertise();
}

static void nimble_host_task(void *param)
{
    ESP_LOGI(BLE_TAG, "BLE Host Task Started");
    nimble_port_run();
    nimble_port_freertos_deinit();
}

/* -------------------------------------------------------------------------- */
/* 5. Initialization Entry Point */
/* -------------------------------------------------------------------------- */
void ble_provisioning_start(void)
{
    ESP_LOGI(BLE_TAG, "Initializing Native BLE provisioning service");

    nimble_port_init();

    /* Initialize the NimBLE host configuration */
    ble_hs_cfg.reset_cb = NULL;
    ble_hs_cfg.sync_cb = ble_app_on_sync;
    ble_hs_cfg.gatts_register_cb = NULL;
    ble_hs_cfg.store_status_cb = ble_store_util_status_rr;

    /* Security Config: LESC enabled, no passkey */
    ble_hs_cfg.sm_bonding = 1;
    ble_hs_cfg.sm_mitm = 1;
    ble_hs_cfg.sm_sc = 1;
    ble_hs_cfg.sm_our_key_dist = 0;
    ble_hs_cfg.sm_their_key_dist = 0;
    ble_hs_cfg.sm_io_cap = BLE_SM_IO_CAP_NO_IO;

    ble_svc_gap_device_name_set("MoleProvision");

    /* Register GATT services */
    ble_svc_gap_init();
    ble_svc_gatt_init();
    int rc = ble_gatts_count_cfg(gatt_svcs);
    if (rc != 0) {
        ESP_LOGE(BLE_TAG, "Error counting gatt resources");
    }
    rc = ble_gatts_add_svcs(gatt_svcs);
    if (rc != 0) {
        ESP_LOGE(BLE_TAG, "Error adding gatt services");
    }

    /* Start the task */
    nimble_port_freertos_init(nimble_host_task);
}
