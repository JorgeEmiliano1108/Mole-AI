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
#include <stdbool.h>
#include "esp_log.h"
#include "esp_random.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "esp_system.h"
#include "cJSON.h"
#include "mole_config.h"
#include "edge_frame.h"
#include "fee2_frame.h"
#include "ble_provisioning.h"

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
/* Characteristic: FEE1 (provisioning WRITE, legacy) */
static const ble_uuid16_t chr_uuid = BLE_UUID16_INIT(0xFEE1);
/* Characteristic: FEE2 (live telemetry READ+NOTIFY, spec gatt-fee2-spec.md) */
static const ble_uuid16_t fee2_uuid = BLE_UUID16_INIT(0xFEE2);

/* ── FEE2 live state (spec §1/§4) ─────────────────────────────────────────── */
static uint16_t s_fee2_attr_handle = 0;
static uint16_t s_conn_handle = BLE_HS_CONN_HANDLE_NONE;
static bool s_live_mode = false;
static bool s_stack_inited = false;
static bool s_synced = false;
static uint32_t s_window_s = 30;
static uint8_t s_fee2_value[FEE2_MAX_FRAME_LEN];
static uint16_t s_fee2_len = 0;

/* Semaphore used by the main task */
extern SemaphoreHandle_t g_provision_sem;

static uint8_t own_addr_type;

/* Forward declarations */
static int gap_event_cb(struct ble_gap_event *event, void *arg);
static int gatt_chr_access_cb(uint16_t conn_handle, uint16_t attr_handle,
                              struct ble_gatt_access_ctxt *ctxt, void *arg);

/* -------------------------------------------------------------------------- */
static int gatt_fee2_access_cb(uint16_t conn_handle, uint16_t attr_handle,
                               struct ble_gatt_access_ctxt *ctxt, void *arg);

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
            {
                /* FEE2: latest frame (READ) + live notify (NOTIFY+CCCD).
                 * NimBLE añade el CCCD 0x2902 automáticamente. */
                .uuid = &fee2_uuid.u,
                .access_cb = gatt_fee2_access_cb,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_NOTIFY,
            },
            { 0 } /* No more characteristics in this service */
        },
    },
    { 0 } /* No more services */
};

/* -------------------------------------------------------------------------- */
/* 1b. FEE2 Access Callback (spec §1: READ vigente, vacío → UNLIKELY) */
/* -------------------------------------------------------------------------- */
static int gatt_fee2_access_cb(uint16_t conn_handle, uint16_t attr_handle,
                               struct ble_gatt_access_ctxt *ctxt, void *arg)
{
    (void)conn_handle;
    (void)attr_handle;
    (void)arg;
    if (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) {
        /* Sin primera muestra (nodo sin provisionar): valor vacío. */
        if (s_fee2_len == 0) return BLE_ATT_ERR_UNLIKELY;
        /* La pila también invoca este READ para serializar el NOTIFY. */
        return os_mbuf_append(ctxt->om, s_fee2_value, s_fee2_len) == 0
            ? 0
            : BLE_ATT_ERR_INSUFFICIENT_RES;
    }
    if (ctxt->op == BLE_GATT_ACCESS_OP_WRITE_CHR) {
        return BLE_ATT_ERR_WRITE_NOT_PERMITTED;
    }
    return 0;
}

/* Captura el value handle de FEE2 para ble_gatts_notify(). */
static void gatts_register_cb(struct ble_gatt_register_ctxt *ctxt, void *arg)
{
    (void)arg;
    if (ctxt->op == BLE_GATT_REGISTER_OP_CHR &&
        ble_uuid_cmp(ctxt->chr.chr_def->uuid, &fee2_uuid.u) == 0) {
        s_fee2_attr_handle = ctxt->chr.val_handle;
        ESP_LOGI(BLE_TAG, "FEE2 chr handle: %d", s_fee2_attr_handle);
    }
}

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
    esp_err_t err = nvs_open(MOLE_NVS_NAMESPACE, NVS_READWRITE, &nvs_handle);
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

                /* Parse JSON payload — expected format:
                 * {"ssid":"...","pass":"...","token":"...","interval":5}
                 */
                cJSON *root = cJSON_Parse(buf);
                if (root) {
                    nvs_handle_t nvs_handle;
                    if (nvs_open(MOLE_NVS_NAMESPACE, NVS_READWRITE, &nvs_handle) == ESP_OK) {
                        cJSON *ssid     = cJSON_GetObjectItem(root, MOLE_BLE_PROV_KEY_SSID);
                        cJSON *pass     = cJSON_GetObjectItem(root, MOLE_BLE_PROV_KEY_PASS);
                        cJSON *token    = cJSON_GetObjectItem(root, MOLE_BLE_PROV_KEY_TOKEN);
                        cJSON *interval = cJSON_GetObjectItem(root, MOLE_BLE_PROV_KEY_INTERVAL);

                        if (ssid     && cJSON_IsString(ssid)     && ssid->valuestring)
                            nvs_set_str(nvs_handle, "wifi_ssid", ssid->valuestring);
                        if (pass     && cJSON_IsString(pass)     && pass->valuestring)
                            nvs_set_str(nvs_handle, "wifi_pass", pass->valuestring);
                        if (token    && cJSON_IsString(token)    && token->valuestring)
                            nvs_set_str(nvs_handle, MOLE_NVS_KEY_TOKEN, token->valuestring);
                        if (interval && cJSON_IsNumber(interval))
                            nvs_set_u32(nvs_handle, "telemetry_int",
                                        (uint32_t)interval->valuedouble);

                        nvs_commit(nvs_handle);
                        nvs_close(nvs_handle);
                        ESP_LOGI(BLE_TAG, "BLE credentials saved to NVS");
                    }
                    cJSON_Delete(root);
                } else {
                    ESP_LOGE(BLE_TAG, "Invalid BLE provisioning JSON: %s", buf);
                }

                free(buf);

                /* Signal main task (triggers reboot from start_captive_portal) */
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
/* 3. GAP Event Callback + Advertising (ventana live vs provisioning) */
/* -------------------------------------------------------------------------- */
static void ble_app_advertise(int32_t duration_ms)
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

    rc = ble_gap_adv_start(own_addr_type, NULL, duration_ms,
                           &adv_params, gap_event_cb, NULL);
    if (rc != 0) {
        ESP_LOGE(BLE_TAG, "Error enabling advertising; rc=%d", rc);
        return;
    }
    ESP_LOGI(BLE_TAG, "BLE advertising started (dur=%ld ms)", (long)duration_ms);
}

static int gap_event_cb(struct ble_gap_event *event, void *arg)
{
    switch (event->type) {
    case BLE_GAP_EVENT_CONNECT:
        ESP_LOGI(BLE_TAG, "BLE central connected, status=%d", event->connect.status);
        if (event->connect.status == 0) {
            s_conn_handle = event->connect.conn_handle;
        } else if (!s_live_mode) {
            /* Solo provisioning reanuncia ante fallo (FOREVER). */
            ble_app_advertise(BLE_HS_FOREVER);
        }
        break;

    case BLE_GAP_EVENT_DISCONNECT:
        ESP_LOGI(BLE_TAG, "BLE central disconnected, reason=%d", event->disconnect.reason);
        s_conn_handle = BLE_HS_CONN_HANDLE_NONE;
        if (!s_live_mode) {
            // Restart advertising (provisioning)
            ble_app_advertise(BLE_HS_FOREVER);
        }
        /* Live: no reanuncia; el FSM apaga el radio y duerme (spec §4). */
        break;

    case BLE_GAP_EVENT_ADV_COMPLETE:
        /* Ventana live expirada: radio off implícito, el FSM duerme. */
        ESP_LOGI(BLE_TAG, "BLE adv window complete (live=%d)", s_live_mode);
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

    s_synced = true;
    if (s_live_mode) {
        ble_app_advertise((int32_t)(s_window_s * 1000U));
    } else {
        ble_app_advertise(BLE_HS_FOREVER);
    }
}

static void nimble_host_task(void *param)
{
    ESP_LOGI(BLE_TAG, "BLE Host Task Started");
    nimble_port_run();
    nimble_port_freertos_deinit();
}

/* -------------------------------------------------------------------------- */
/* 5. Initialization Entry Point + Live API (spec §4) */
/* -------------------------------------------------------------------------- */
static void ble_stack_init_once(void)
{
    if (s_stack_inited) return;
    s_stack_inited = true;

    nimble_port_init();

    /* Initialize the NimBLE host configuration */
    ble_hs_cfg.reset_cb = NULL;
    ble_hs_cfg.sync_cb = ble_app_on_sync;
    ble_hs_cfg.gatts_register_cb = gatts_register_cb;
    ble_hs_cfg.store_status_cb = ble_store_util_status_rr;

    /* Security Config: LESC enabled, no passkey */
    ble_hs_cfg.sm_bonding = 1;
    ble_hs_cfg.sm_mitm = 1;
    ble_hs_cfg.sm_sc = 1;
    ble_hs_cfg.sm_our_key_dist = 0;
    ble_hs_cfg.sm_their_key_dist = 0;
    ble_hs_cfg.sm_io_cap = BLE_SM_IO_CAP_NO_IO;

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

void ble_provisioning_start(void)
{
    ESP_LOGI(BLE_TAG, "Initializing Native BLE provisioning service");

    s_live_mode = false;
    ble_svc_gap_device_name_set("MoleProvision");
    ble_stack_init_once();
}

/* Ventana live al despertar (spec §4): anuncia `window_s` y vuelve a dormir.
 * Llamar una vez por ciclo de wake tras muestrear. No bloquea. */
void ble_live_start(uint32_t window_s)
{
    ESP_LOGI(BLE_TAG, "BLE live window: %lu s", (unsigned long)window_s);

    s_live_mode = true;
    s_window_s = (window_s == 0) ? BLE_ADV_WINDOW_S : window_s;
    ble_svc_gap_device_name_set(MOLE_NODE_NAME);
    ble_stack_init_once();
    if (s_synced) {
        ble_app_advertise((int32_t)(s_window_s * 1000U));
    }
    /* Si el host aún sincroniza, on_sync anunciará la ventana. */
}

/* Cierra la ventana live antes del deep-sleep (spec §4). Idempotente. */
void ble_live_stop(void)
{
    if (!s_live_mode) return;
    int rc = ble_gap_adv_stop();
    if (rc != 0 && rc != BLE_HS_EALREADY) {
        ESP_LOGW(BLE_TAG, "ble_gap_adv_stop rc=%d", rc);
    }
    s_conn_handle = BLE_HS_CONN_HANDLE_NONE;
}

/* Codifica y publica la última trama; notifica al central suscrito
 * (best-effort). Retorna bytes codificados o -1. Sin tokens/PII. */
int ble_fee2_publish(const edge_frame_t *frame)
{
    int len = fee2_encode(frame, s_fee2_value, sizeof(s_fee2_value));
    if (len < 0) {
        ESP_LOGE(BLE_TAG, "FEE2 encode failed");
        return -1;
    }
    s_fee2_len = (uint16_t)len;
    if (s_conn_handle != BLE_HS_CONN_HANDLE_NONE && s_fee2_attr_handle != 0) {
        int rc = ble_gatts_notify(s_conn_handle, s_fee2_attr_handle);
        if (rc != 0) {
            ESP_LOGW(BLE_TAG, "FEE2 notify rc=%d (sin suscripción?)", rc);
        }
    }
    return len;
}
