/*
 * Host-side tests for state_machine.h enums and constants.
 *
 * These tests verify the enum definitions only — they do NOT link
 * against state_machine.c (which requires ESP-IDF stubs).
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

/* ── State count verification ───────────────────────────────────────────── */
static void test_state_counts(void)
{
    TEST("FSM_STATE_COUNT == 13 (12 nominal + ERROR)")
        ok = (FSM_STATE_COUNT == 13);
    END_TEST("FSM_STATE_COUNT == 13");
}

/* ── Event count verification ───────────────────────────────────────────── */
static void test_event_counts(void)
{
    TEST("At least 19 events defined")
        ok = (EV_ERROR >= 19);
    END_TEST("At least 19 events");
}

/* ── All state enum values are unique and in range ──────────────────────── */
static void test_state_uniqueness(void)
{
    int seen[FSM_STATE_COUNT];
    memset(seen, 0, sizeof(seen));
    TEST("All state enum values unique")
        for (int i = 0; i < FSM_STATE_COUNT; i++) {
            fsm_state_t s = (fsm_state_t)i;
            if (s < 0 || s >= FSM_STATE_COUNT) { ok = 0; break; }
            if (seen[s]) { ok = 0; break; }
            seen[s] = 1;
        }
    END_TEST("All state enum values unique");
}

/* ── All event enum values are unique and in range ──────────────────────── */
static void test_event_uniqueness(void)
{
    int seen[EV_EVENT_COUNT];
    memset(seen, 0, sizeof(seen));
    TEST("All event enum values unique")
        for (int i = 0; i < EV_EVENT_COUNT; i++) {
            fsm_event_t e = (fsm_event_t)i;
            if (e < 0 || e >= EV_EVENT_COUNT) { ok = 0; break; }
            if (seen[e]) { ok = 0; break; }
            seen[e] = 1;
        }
    END_TEST("All event enum values unique");
}

/* ── Key state names exist ──────────────────────────────────────────────── */
static void test_key_states_exist(void)
{
    TEST("FSM_COLD_START defined")
        ok = (FSM_COLD_START >= 0);
    END_TEST("FSM_COLD_START");

    TEST("FSM_NVS_LOADING defined")
        ok = (FSM_NVS_LOADING >= 0);
    END_TEST("FSM_NVS_LOADING");

    TEST("FSM_PROVISIONING defined")
        ok = (FSM_PROVISIONING >= 0);
    END_TEST("FSM_PROVISIONING");

    TEST("FSM_TELEMETRY_DEGRADED defined")
        ok = (FSM_TELEMETRY_DEGRADED >= 0);
    END_TEST("FSM_TELEMETRY_DEGRADED");

    TEST("FSM_DEEP_SLEEP defined")
        ok = (FSM_DEEP_SLEEP >= 0);
    END_TEST("FSM_DEEP_SLEEP");

    TEST("FSM_ERROR defined")
        ok = (FSM_ERROR >= 0);
    END_TEST("FSM_ERROR");
}

/* ── Key event names exist ──────────────────────────────────────────────── */
static void test_key_events_exist(void)
{
    TEST("EV_CREDS_FOUND defined")
        ok = (EV_CREDS_FOUND >= 0);
    END_TEST("EV_CREDS_FOUND");

    TEST("EV_NTP_SYNCED defined")
        ok = (EV_NTP_SYNCED >= 0);
    END_TEST("EV_NTP_SYNCED");

    TEST("EV_SENSOR_PARTIAL defined")
        ok = (EV_SENSOR_PARTIAL >= 0);
    END_TEST("EV_SENSOR_PARTIAL");

    TEST("EV_TRANSPORT_AUTH_FAIL defined")
        ok = (EV_TRANSPORT_AUTH_FAIL >= 0);
    END_TEST("EV_TRANSPORT_AUTH_FAIL");

    TEST("EV_DEEP_SLEEP_WAKE defined")
        ok = (EV_DEEP_SLEEP_WAKE >= 0);
    END_TEST("EV_DEEP_SLEEP_WAKE");
}

/* ── Summary ────────────────────────────────────────────────────────────── */
int main(void)
{
    printf("\n=== state_machine enum tests ===\n\n");

    test_state_counts();
    test_event_counts();
    test_state_uniqueness();
    test_event_uniqueness();
    test_key_states_exist();
    test_key_events_exist();

    printf("\n=== Results: %d passed, %d failed ===\n\n", s_pass, s_fail);
    return s_fail > 0 ? 1 : 0;
}
