/*
 * Host-side behavioral tests for state_machine.c
 *
 * Links against state_machine.c using ESP-IDF stubs.
 */
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include "state_machine.h"

static int s_pass = 0, s_fail = 0;

#define TEST(name_) do { \
    printf("  TEST: %s ... ", name_); \
    int ok = 1;

#define END_TEST(name_) \
    if (ok) { s_pass++; printf("PASS\n"); } \
    else    { s_fail++; printf("FAIL\n"); } \
} while(0)

/* ─── fsm_init creates context and queue ──────────────────────────────── */
static void test_fsm_init_basic(void)
{
    fsm_context_t *ctx = fsm_init();
    TEST("fsm_init returns non-NULL")
        ok = (ctx != NULL);
    END_TEST("fsm_init non-NULL");

    TEST("fsm_init creates event queue")
        ok = (ctx && ctx->event_queue != NULL);
    END_TEST("fsm_init event queue");

    TEST("fsm_init initial state is COLD_START")
        ok = (ctx && ctx->current == FSM_COLD_START);
    END_TEST("fsm_init COLD_START");

    TEST("fsm_get_queue matches ctx->event_queue")
        ok = (ctx && fsm_get_queue(ctx) == ctx->event_queue);
    END_TEST("fsm_get_queue matches");
}

/* ─── EV_NONE dispatch on COLD_START → NVS_LOADING ───────────────────── */
static void test_transition_cold_start_to_nvs_loading(void)
{
    fsm_context_t *ctx = fsm_init();
    TEST("COLD_START + EV_NONE → NVS_LOADING")
        fsm_dispatch(ctx, EV_NONE);
        ok = (ctx->current == FSM_NVS_LOADING);
    END_TEST("COLD_START → NVS_LOADING");
}

/* ─── Post event via queue is received by fsm_dispatch ────────────────── */
static void test_queue_event_dispatch(void)
{
    fsm_context_t *ctx = fsm_init();
    QueueHandle_t q = fsm_get_queue(ctx);

    /* Move to NVS_LOADING first — drain the resulting EV_CREDS_MISSING */
    fsm_dispatch(ctx, EV_NONE);
    fsm_event_t drain;
    while (xQueueReceive(q, &drain, 0) == pdTRUE) {}

    /* Now manually test: post EV_WIFI_CONNECTED to a context in WIFI_CONNECT.
     * Start by forcing the state to WIFI_CONNECT. */
    ctx->current = FSM_WIFI_CONNECT;

    /* Post the event and receive it */
    fsm_event_t ev = EV_WIFI_CONNECTED;
    xQueueSend(q, &ev, 0);

    fsm_event_t received;
    if (xQueueReceive(q, &received, 0) == pdTRUE) {
        printf("  [debug] received event=%d\n", (int)received);
        fsm_dispatch(ctx, received);
    }

    TEST("EV_WIFI_CONNECTED → FSM_NTP_SYNC")
        printf("  [debug] current state=%d (expected NTP_SYNC=%d)\n",
               (int)ctx->current, (int)FSM_NTP_SYNC);
        ok = (ctx->current == FSM_NTP_SYNC);
    END_TEST("EV_WIFI_CONNECTED → NTP_SYNC");
}

/* ─── EV_CREDS_FOUND from NVS_LOADING → WIFI_CONNECT ──────────────────── */
static void test_creds_found_transition(void)
{
    fsm_context_t *ctx = fsm_init();
    QueueHandle_t q = fsm_get_queue(ctx);

    fsm_dispatch(ctx, EV_NONE);
    fsm_event_t drain;
    while (xQueueReceive(q, &drain, 0) == pdTRUE) {}

    ctx->current = FSM_NVS_LOADING;
    fsm_event_t ev = EV_CREDS_FOUND;
    xQueueSend(q, &ev, 0);

    fsm_event_t received;
    if (xQueueReceive(q, &received, 0) == pdTRUE) {
        fsm_dispatch(ctx, received);
    }

    TEST("EV_CREDS_FOUND → FSM_WIFI_CONNECT")
        ok = (ctx->current == FSM_WIFI_CONNECT);
    END_TEST("EV_CREDS_FOUND → WIFI_CONNECT");
}

/* ─── Unknown event in state does not change state ────────────────────── */
static void test_unknown_event(void)
{
    fsm_context_t *ctx = fsm_init();
    fsm_dispatch(ctx, EV_NONE);  /* → NVS_LOADING */

    fsm_state_t before = ctx->current;
    fsm_dispatch(ctx, (fsm_event_t)99);  /* EV_ERROR or invalid */

    TEST("Unknown event keeps current state")
        ok = (ctx->current == before);
    END_TEST("Unknown event keeps state");
}

/* ─── Summary ─────────────────────────────────────────────────────────── */
int main(void)
{
    printf("\n=== state_machine behavioral tests ===\n\n");

    test_fsm_init_basic();
    test_transition_cold_start_to_nvs_loading();
    test_queue_event_dispatch();
    test_creds_found_transition();
    test_unknown_event();

    printf("\n=== Results: %d passed, %d failed ===\n\n", s_pass, s_fail);
    return s_fail > 0 ? 1 : 0;
}
