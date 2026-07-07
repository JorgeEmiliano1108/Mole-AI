/*
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * state_machine.c — 12-state FSM for Mole.AI Telemetry Node.
 *
 * Architecture:
 *   - Dedicated fsm_task blocks on xQueueReceive for events.
 *   - Event handlers (WiFi, transport) post events to the FSM queue.
 *   - Transition table in flash — (state × event) → action + new_state.
 *   - Actions run synchronously within fsm_dispatch; they may post new
 *     events to the queue for subsequent processing.
 *   - NVS persist on every state change.
 */
#include <string.h>
#include "esp_log.h"
#include "esp_system.h"
#include "esp_task_wdt.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "mole_config.h"
#include "state_machine.h"
#include "offline_buffer.h"
#include "sensor_frame.h"
#include "mole_ntp.h"
#include "ble_provisioning.h"

/* ── NVS keys ───────────────────────────────────────────────────────────── */
#define NVS_KEY_LAST_STATE      "last_state"
#define NVS_KEY_DEGRADED        "degraded_sens"
#define NVS_KEY_RECONNECT_CNT   "fsm_reconnect_cnt"
#define NVS_KEY_BUFFERED_CNT    "buffered_cnt"

static const char *TAG = "FSM";

/* ── Context singleton ──────────────────────────────────────────────────── */
static fsm_context_t s_ctx;

/* ── Event queue helpers ────────────────────────────────────────────────── */
static void post_event(fsm_context_t *ctx, fsm_event_t ev)
{
    if (ctx && ctx->event_queue) {
        xQueueSend(ctx->event_queue, &ev, 0);
    }
}

/* ══════════════════════════════════════════════════════════════════════════
 *  Action Functions
 *
 *  Each action is called by fsm_dispatch when a transition fires.
 *  Actions may call blocking operations (the FSM task is a dedicated task,
 *  NOT the event loop).  On completion, actions post events for the FSM
 *  loop to pick up on the next iteration.
 * ══════════════════════════════════════════════════════════════════════════ */

static void act_nvs_check(fsm_context_t *ctx)
{
    fsm_load_nvs(ctx);

    /* Check NVS for credentials */
    nvs_handle_t h;
    bool has_token = false;
    if (nvs_open(MOLE_NVS_NAMESPACE, NVS_READONLY, &h) == ESP_OK) {
        char buf[8] = {0};
        size_t sz = sizeof(buf);
        has_token = (nvs_get_str(h, MOLE_NVS_KEY_TOKEN, buf, &sz) == ESP_OK
                     && sz > 1);
        nvs_close(h);
    }

    if (has_token) {
        ESP_LOGI(TAG, "NVS: credentials found");
        post_event(ctx, EV_CREDS_FOUND);
    } else {
        ESP_LOGW(TAG, "NVS: credentials missing");
        post_event(ctx, EV_CREDS_MISSING);
    }
}

static void act_start_provisioning(fsm_context_t *ctx)
{
    extern void start_captive_portal(void);

    ESP_LOGI(TAG, "Entering provisioning mode");
    ble_provisioning_start();

    /* Create semaphore if not already */
    if (!g_provision_sem) {
        g_provision_sem = xSemaphoreCreateBinary();
    }

    start_captive_portal();  /* blocks until provisioning completes, then
                              * calls esp_restart() — unreachable after */
    (void)ctx;
}

static void act_start_wifi(fsm_context_t *ctx)
{
    extern void wifi_init_sta(void);
    wifi_init_sta();  /* non-blocking — starts WiFi, returns immediately */
    /* The wifi_event_handler will post EV_WIFI_CONNECTED when IP is obtained */
    (void)ctx;
}

static void act_start_ntp(fsm_context_t *ctx)
{
    esp_err_t err = mole_ntp_init();
    if (err == ESP_OK) {
        mole_ntp_wait_sync(10000);
        post_event(ctx, EV_NTP_SYNCED);
    } else {
        ESP_LOGW(TAG, "NTP init failed — continuing without sync");
        post_event(ctx, EV_NTP_TIMEOUT);
    }
    (void)ctx;
}

static void act_init_sensors(fsm_context_t *ctx)
{
    extern void sensor_init_all(void);
    extern int  sensor_get_degraded_bitmask(void);

    sensor_init_all();
    ctx->degraded_sensors = (uint8_t)sensor_get_degraded_bitmask();

    if (ctx->degraded_sensors == 0) {
        ESP_LOGI(TAG, "All sensors OK");
        post_event(ctx, EV_SENSOR_OK);
    } else {
        ESP_LOGW(TAG, "Sensor degraded: 0x%02x", ctx->degraded_sensors);
        post_event(ctx, EV_SENSOR_PARTIAL);
    }
}

static void act_start_transport(fsm_context_t *ctx)
{
    extern void transport_init_and_connect(void);
    transport_init_and_connect();  /* posts EV_TRANSPORT_CONNECTED / _DISCONNECT / _AUTH_FAIL */
    (void)ctx;
}

static void act_send_telemetry(fsm_context_t *ctx)
{
    extern void transport_send_payload(void);
    transport_send_payload();  /* posts EV_SEND_OK / _AUTH_FAIL / _SEND_FAIL */
    (void)ctx;
}

static void act_enter_reconnecting(fsm_context_t *ctx)
{
    extern void start_backoff_timer(void);
    start_backoff_timer();
    (void)ctx;
}

static void act_buffer_sample(fsm_context_t *ctx)
{
    ctx->buffered_count++;
    ESP_LOGI(TAG, "Buffered sample (%d stored)", ctx->buffered_count);
    (void)ctx;
}

static void act_drain_and_sleep(fsm_context_t *ctx)
{
    extern void transport_send_frame_from_buffer(const sensor_frame_t *frame);
    extern void enter_deep_sleep(void);

    while (offline_buffer_count() > 0) {
        sensor_frame_t frame;
        if (!offline_buffer_pop(&frame)) break;
        transport_send_frame_from_buffer(&frame);
    }

    fsm_persist_nvs(ctx);
    enter_deep_sleep();  /* does not return */
}

static void act_enter_error(fsm_context_t *ctx)
{
    ESP_LOGE(TAG, "FSM: unrecoverable error — rebooting");
    fsm_persist_nvs(ctx);
    esp_restart();       /* does not return */
}

static void act_persist_and_reboot(fsm_context_t *ctx)
{
    fsm_persist_nvs(ctx);
    ESP_LOGI(TAG, "Provisioning complete — rebooting");
    esp_restart();
}

/* ══════════════════════════════════════════════════════════════════════════
 *  Transition Table  (flash resident)
 * ══════════════════════════════════════════════════════════════════════════ */
typedef struct {
    fsm_state_t  from;
    fsm_event_t  event;
    fsm_state_t  to;
    void       (*action)(fsm_context_t *);
} fsm_transition_t;

#define T(from_, event_, to_, action_) \
    { .from = from_, .event = event_, .to = to_, .action = action_ }

static const fsm_transition_t s_transitions[] = {
    /* COLD_START → NVS_LOADING (initial scan) */
    T(FSM_COLD_START,           EV_NONE,              FSM_NVS_LOADING,          act_nvs_check),

    /* NVS_LOADING → WiFi or provisioning */
    T(FSM_NVS_LOADING,          EV_CREDS_FOUND,       FSM_WIFI_CONNECT,         act_start_wifi),
    T(FSM_NVS_LOADING,          EV_CREDS_MISSING,     FSM_PROVISIONING,         act_start_provisioning),

    /* PROVISIONING: done → reboot into COLD_START */
    T(FSM_PROVISIONING,         EV_CREDS_SAVED,       FSM_COLD_START,           act_persist_and_reboot),

    /* WIFI_CONNECT → NTP or reconnect */
    T(FSM_WIFI_CONNECT,         EV_WIFI_CONNECTED,    FSM_NTP_SYNC,             act_start_ntp),
    T(FSM_WIFI_CONNECT,         EV_WIFI_DISCONNECT,   FSM_RECONNECTING,         act_enter_reconnecting),

    /* NTP_SYNC → sensor init (continue even on timeout) */
    T(FSM_NTP_SYNC,             EV_NTP_SYNCED,        FSM_SENSOR_INIT,          act_init_sensors),
    T(FSM_NTP_SYNC,             EV_NTP_TIMEOUT,       FSM_SENSOR_INIT,          act_init_sensors),

    /* SENSOR_INIT → transport or degraded */
    T(FSM_SENSOR_INIT,          EV_SENSOR_OK,         FSM_TRANSPORT_CONNECTING, act_start_transport),
    T(FSM_SENSOR_INIT,          EV_SENSOR_PARTIAL,    FSM_TRANSPORT_CONNECTING, act_start_transport),
    T(FSM_SENSOR_INIT,          EV_SENSOR_FAIL,       FSM_TELEMETRY_DEGRADED,   act_start_transport),

    /* TRANSPORT_CONNECTING → telemetry, reconnect, or error */
    T(FSM_TRANSPORT_CONNECTING, EV_TRANSPORT_CONNECTED,    FSM_TELEMETRY_SENDING,   act_send_telemetry),
    T(FSM_TRANSPORT_CONNECTING, EV_TRANSPORT_DISCONNECT,   FSM_RECONNECTING,        act_enter_reconnecting),
    T(FSM_TRANSPORT_CONNECTING, EV_TRANSPORT_AUTH_FAIL,    FSM_ERROR,               act_enter_error),

    /* TELEMETRY_SENDING → deep sleep, reconnect, or error */
    T(FSM_TELEMETRY_SENDING,    EV_SEND_OK,               FSM_DEEP_SLEEP,          act_drain_and_sleep),
    T(FSM_TELEMETRY_SENDING,    EV_SEND_FAIL,             FSM_RECONNECTING,        act_enter_reconnecting),
    T(FSM_TELEMETRY_SENDING,    EV_TRANSPORT_DISCONNECT,  FSM_RECONNECTING,        act_enter_reconnecting),
    T(FSM_TELEMETRY_SENDING,    EV_TRANSPORT_AUTH_FAIL,   FSM_ERROR,               act_enter_error),

    /* TELEMETRY_DEGRADED → send degraded payload, deep sleep, or reconnect */
    T(FSM_TELEMETRY_DEGRADED,   EV_TRANSPORT_CONNECTED,   FSM_TELEMETRY_SENDING,   act_send_telemetry),
    T(FSM_TELEMETRY_DEGRADED,   EV_SEND_OK,               FSM_DEEP_SLEEP,          act_drain_and_sleep),
    T(FSM_TELEMETRY_DEGRADED,   EV_SEND_FAIL,             FSM_RECONNECTING,        act_enter_reconnecting),

    /* RECONNECTING → NTP (WiFi restored) or offline buffer (exceeded) */
    T(FSM_RECONNECTING,         EV_WIFI_CONNECTED,        FSM_NTP_SYNC,            act_start_ntp),
    T(FSM_RECONNECTING,         EV_RECONNECT_EXCEEDED,    FSM_OFFLINE_BUFFER,      act_buffer_sample),

    /* OFFLINE_BUFFER → WiFi when restored */
    T(FSM_OFFLINE_BUFFER,       EV_WIFI_RESTORED,         FSM_WIFI_CONNECT,        act_start_wifi),

    /* DEEP_SLEEP → WiFi on wake */
    T(FSM_DEEP_SLEEP,           EV_DEEP_SLEEP_WAKE,       FSM_WIFI_CONNECT,        act_start_wifi),
};

static const int s_transition_count = sizeof(s_transitions) / sizeof(s_transitions[0]);

/* ══════════════════════════════════════════════════════════════════════════
 *  Public API
 * ══════════════════════════════════════════════════════════════════════════ */

fsm_context_t* fsm_init(void)
{
    memset(&s_ctx, 0, sizeof(s_ctx));
    s_ctx.event_queue = xQueueCreate(8, sizeof(fsm_event_t));
    if (!s_ctx.event_queue) {
        ESP_LOGE(TAG, "Failed to create FSM event queue");
        return NULL;
    }
    s_ctx.current          = FSM_COLD_START;
    s_ctx.last_persisted   = FSM_COLD_START;

    if (!offline_buffer_init(30)) {
        ESP_LOGW(TAG, "Offline buffer init failed — continuing without");
    }

    ESP_LOGI(TAG, "FSM initialized");
    return &s_ctx;
}

QueueHandle_t fsm_get_queue(fsm_context_t *ctx)
{
    return ctx ? ctx->event_queue : NULL;
}

void fsm_dispatch(fsm_context_t *ctx, fsm_event_t ev)
{
    if (!ctx) return;

    for (int i = 0; i < s_transition_count; i++) {
        const fsm_transition_t *t = &s_transitions[i];
        if (t->from == ctx->current && t->event == ev) {
            ESP_LOGI(TAG, "S%-2d --[E%-2d]--> S%-2d",
                     (int)t->from, (int)ev, (int)t->to);
            ctx->current = t->to;
            if (t->action) t->action(ctx);
            return;
        }
    }

    ESP_LOGW(TAG, "No transition: state=%d event=%d",
             (int)ctx->current, (int)ev);
}

void fsm_persist_nvs(fsm_context_t *ctx)
{
    if (!ctx) return;
    nvs_handle_t h;
    if (nvs_open(MOLE_NVS_NAMESPACE, NVS_READWRITE, &h) != ESP_OK) return;

    uint8_t state_u8 = (uint8_t)ctx->current;
    nvs_set_u8(h, NVS_KEY_LAST_STATE, state_u8);
    nvs_set_u8(h, NVS_KEY_DEGRADED,  ctx->degraded_sensors);
    nvs_set_i32(h, NVS_KEY_RECONNECT_CNT, ctx->reconnect_count);
    nvs_set_u8(h, NVS_KEY_BUFFERED_CNT,   ctx->buffered_count);
    nvs_commit(h);
    nvs_close(h);

    ctx->last_persisted = ctx->current;
}

void fsm_load_nvs(fsm_context_t *ctx)
{
    if (!ctx) return;
    nvs_handle_t h;
    if (nvs_open(MOLE_NVS_NAMESPACE, NVS_READONLY, &h) != ESP_OK) return;

    uint8_t u8 = 0;
    int32_t i32 = 0;
    nvs_get_u8(h, NVS_KEY_LAST_STATE, &u8);
    if (u8 < FSM_STATE_COUNT) ctx->last_persisted = (fsm_state_t)u8;
    u8 = 0;
    nvs_get_u8(h, NVS_KEY_DEGRADED, &u8);
    ctx->degraded_sensors = u8;
    i32 = 0;
    nvs_get_i32(h, NVS_KEY_RECONNECT_CNT, &i32);
    ctx->reconnect_count = (int)i32;
    u8 = 0;
    nvs_get_u8(h, NVS_KEY_BUFFERED_CNT, &u8);
    ctx->buffered_count = u8;
    nvs_close(h);

    ESP_LOGI(TAG, "NVS: last_state=%d degraded=0x%02x reconnect=%d buffered=%d",
             (int)ctx->last_persisted, ctx->degraded_sensors,
             ctx->reconnect_count, ctx->buffered_count);

    /* If waking from deep sleep, skip cold boot */
    if (ctx->last_persisted == FSM_DEEP_SLEEP) {
        ctx->current = FSM_DEEP_SLEEP;
    }
}

/* ══════════════════════════════════════════════════════════════════════════
 *  fsm_task — main FreeRTOS task running the FSM loop
 * ══════════════════════════════════════════════════════════════════════════ */

void fsm_task(void *arg)
{
    fsm_context_t *ctx = (fsm_context_t *)arg;
    if (!ctx) {
        ESP_LOGE(TAG, "fsm_task: NULL context");
        vTaskDelete(NULL);
        return;
    }

    ESP_LOGI(TAG, "FSM task started — state=%d", (int)ctx->current);

    /* Kick off initial auto-transition (COLD_START → NVS_LOADING) */
    fsm_dispatch(ctx, EV_NONE);

    while (1) {
        fsm_event_t ev;

        /* Block indefinitely until an event arrives (no polling tick) */
        if (xQueueReceive(ctx->event_queue, &ev, portMAX_DELAY) == pdTRUE
            && ev != EV_NONE) {
            esp_task_wdt_reset();
            fsm_dispatch(ctx, ev);
        }
    }
}
