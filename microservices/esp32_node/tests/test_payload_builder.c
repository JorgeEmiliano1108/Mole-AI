/*
 * Host-side unit tests for payload_builder (VS1a)
 * Compile: gcc -I../main/include -I../managed_components/espressif__cjson/cJSON
 *              test_payload_builder.c ../main/payload_builder.c \
 *              ../managed_components/espressif__cjson/cJSON/cJSON.c -lm -o test.elf
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "cJSON.h"
#include "mole_config.h"
#include "edge_frame.h"
#include "payload_builder.h"

static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) do { printf("  TEST: %s ... ", name); } while(0)
#define PASS() do { printf("PASS\n"); tests_passed++; } while(0)
#define FAIL(msg) do { printf("FAIL: %s\n", msg); tests_failed++; } while(0)
#define ASSERT(cond, msg) do { \
    if (!(cond)) { FAIL(msg); return; } \
} while(0)

/* ── Test 1: Basic full frame → produces valid JSON ───────────────────────── */
static void test_payload_basic(void) {
    TEST("basic full frame");

    edge_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.ts = 1699123456.789;
    frame.report_interval_minutes = 5;
    frame.ambient_valid = 0x0F;  /* all 4 ambient fields present */
    frame.ambient.t = 28.4f;
    frame.ambient.h = 65.2f;
    frame.ambient.l = 410.0f;
    frame.ambient.u = 5.5f;
    frame.soil[0].pin = "32";
    frame.soil[0].adc_raw = 2847;
    frame.soil[1].pin = "33";
    frame.soil[1].adc_raw = 3012;
    frame.soil_count = 2;

    char buf[PAYLOAD_BUFFER_SIZE];
    int len = payload_build(&frame, buf, sizeof(buf));
    ASSERT(len > 0, "payload_build returned <= 0");

    cJSON *root = cJSON_Parse(buf);
    ASSERT(root != NULL, "JSON parse failed");

    cJSON *ts = cJSON_GetObjectItem(root, "ts");
    ASSERT(ts != NULL && ts->valuedouble == 1699123456.789, "ts mismatch");

    cJSON *ri = cJSON_GetObjectItem(root, "ri");
    ASSERT(ri != NULL && ri->valueint == 5, "ri mismatch");

    cJSON *a = cJSON_GetObjectItem(root, "a");
    ASSERT(a != NULL, "missing 'a' object");
    cJSON *t = cJSON_GetObjectItem(a, "t");
    ASSERT(t != NULL, "missing 'a.t'");

    cJSON *s = cJSON_GetObjectItem(root, "s");
    ASSERT(s != NULL && cJSON_GetArraySize(s) == 2, "s array size != 2");

    cJSON *dg = cJSON_GetObjectItem(root, "dg");
    ASSERT(dg != NULL && dg->valueint == 0, "dg should be 0 (all sensors OK)");

    cJSON_Delete(root);
    PASS();
}

/* ── Test 2: Partial ambient (only temp + hum) ────────────────────────────── */
static void test_payload_partial(void) {
    TEST("partial ambient (t, h only)");

    edge_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.ts = 1700000000.0;
    frame.report_interval_minutes = 10;
    frame.ambient_valid = AMBIENT_VALID_TEMP_BIT | AMBIENT_VALID_HUM_BIT;
    frame.ambient.t = 25.0f;
    frame.ambient.h = 70.0f;
    /* l and u are uninitialized — should not appear */

    char buf[PAYLOAD_BUFFER_SIZE];
    int len = payload_build(&frame, buf, sizeof(buf));
    ASSERT(len > 0, "payload_build returned <= 0");

    cJSON *root = cJSON_Parse(buf);
    ASSERT(root != NULL, "JSON parse failed");

    cJSON *a = cJSON_GetObjectItem(root, "a");
    ASSERT(a != NULL, "missing 'a'");
    ASSERT(cJSON_GetObjectItem(a, "t") != NULL, "missing 'a.t'");
    ASSERT(cJSON_GetObjectItem(a, "h") != NULL, "missing 'a.h'");
    ASSERT(cJSON_GetObjectItem(a, "l") == NULL, "'a.l' should not appear");
    ASSERT(cJSON_GetObjectItem(a, "u") == NULL, "'a.u' should not appear");

    cJSON *dg = cJSON_GetObjectItem(root, "dg");
    ASSERT(dg != NULL && dg->valueint == 0x0C, "dg should be 0x0C (l+u missing)");

    cJSON_Delete(root);
    PASS();
}

/* ── Test 3: No soil sensors ──────────────────────────────────────────────── */
static void test_payload_no_soil(void) {
    TEST("no soil sensors");

    edge_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.ts = 1700000000.0;
    frame.report_interval_minutes = 5;
    frame.ambient_valid = 0x0F;
    frame.ambient.t = 22.0f;
    frame.ambient.h = 55.0f;
    frame.ambient.l = 300.0f;
    frame.ambient.u = 2.0f;
    frame.soil_count = 0;

    char buf[PAYLOAD_BUFFER_SIZE];
    int len = payload_build(&frame, buf, sizeof(buf));
    ASSERT(len > 0, "payload_build returned <= 0");

    cJSON *root = cJSON_Parse(buf);
    ASSERT(root != NULL, "JSON parse failed");

    cJSON *s = cJSON_GetObjectItem(root, "s");
    ASSERT(s == NULL, "'s' should not appear when soil_count == 0");

    cJSON_Delete(root);
    PASS();
}

/* ── Test 4: Buffer overflow detection ────────────────────────────────────── */
static void test_payload_overflow(void) {
    TEST("buffer too small -> -1");

    edge_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.ts = 1700000000.0;
    frame.report_interval_minutes = 5;
    frame.ambient_valid = 0x0F;

    char tiny_buf[16];
    int len = payload_build(&frame, tiny_buf, sizeof(tiny_buf));
    ASSERT(len < 0, "should return -1 for tiny buffer");

    PASS();
}

/* ── Test 5: dg bitmask calculation ───────────────────────────────────────── */
static void test_payload_dg_bitmask(void) {
    TEST("dg bitmask correctness");

    edge_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.ts = 1700000000.0;
    frame.report_interval_minutes = 5;
    /* Only temp and uv valid → bits 0 and 3 */
    frame.ambient_valid = AMBIENT_VALID_TEMP_BIT | AMBIENT_VALID_UV_BIT;
    frame.ambient.t = 30.0f;
    frame.ambient.u = 8.0f;

    char buf[PAYLOAD_BUFFER_SIZE];
    int len = payload_build(&frame, buf, sizeof(buf));
    ASSERT(len > 0, "payload_build returned <= 0");

    cJSON *root = cJSON_Parse(buf);
    ASSERT(root != NULL, "JSON parse failed");

    /* dg = ~ambient_valid & 0x0F = ~0x09 & 0x0F = 0x06 (h+l missing) */
    cJSON *dg = cJSON_GetObjectItem(root, "dg");
    ASSERT(dg != NULL && dg->valueint == 0x06,
           "dg should be 0x06 (hum+light missing)");

    /* Verify only t and u appear in 'a' */
    cJSON *a = cJSON_GetObjectItem(root, "a");
    ASSERT(a != NULL, "missing 'a'");
    ASSERT(cJSON_GetObjectItem(a, "t") != NULL, "missing 'a.t'");
    ASSERT(cJSON_GetObjectItem(a, "u") != NULL, "missing 'a.u'");
    ASSERT(cJSON_GetObjectItem(a, "h") == NULL, "'a.h' should be absent");
    ASSERT(cJSON_GetObjectItem(a, "l") == NULL, "'a.l' should be absent");

    cJSON_Delete(root);
    PASS();
}

/* ── Test 6: Max soil pins ────────────────────────────────────────────────── */
static void test_payload_max_soil(void) {
    TEST("max soil pins");

    edge_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.ts = 1700000000.0;
    frame.report_interval_minutes = 5;
    frame.ambient_valid = 0x0F;
    frame.ambient.t = 25.0f;
    frame.ambient.h = 60.0f;
    frame.ambient.l = 500.0f;
    frame.ambient.u = 3.0f;

    const char *pins[] = {"32","33","34","35","36","37","38","39"};
    for (int i = 0; i < 8; i++) {
        frame.soil[i].pin = pins[i];
        frame.soil[i].adc_raw = 2000 + i * 100;
    }
    frame.soil_count = 8;

    char buf[PAYLOAD_BUFFER_SIZE];
    int len = payload_build(&frame, buf, sizeof(buf));
    ASSERT(len > 0, "payload_build returned <= 0");

    cJSON *root = cJSON_Parse(buf);
    ASSERT(root != NULL, "JSON parse failed");

    cJSON *s = cJSON_GetObjectItem(root, "s");
    ASSERT(s != NULL && cJSON_GetArraySize(s) == 8, "expected 8 soil items");

    cJSON_Delete(root);
    PASS();
}

/* ── Test 7: Null pin should not crash ────────────────────────────────────── */
static void test_payload_null_pin(void) {
    TEST("null pin fallback");

    edge_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.ts = 1700000000.0;
    frame.report_interval_minutes = 5;
    frame.ambient_valid = 0x0F;
    frame.soil[0].pin = NULL;  /* should fallback to "?" */
    frame.soil[0].adc_raw = 2048;
    frame.soil_count = 1;

    char buf[PAYLOAD_BUFFER_SIZE];
    int len = payload_build(&frame, buf, sizeof(buf));
    ASSERT(len > 0, "payload_build returned <= 0");

    cJSON *root = cJSON_Parse(buf);
    ASSERT(root != NULL, "JSON parse failed");

    cJSON *s = cJSON_GetObjectItem(root, "s");
    ASSERT(s != NULL && cJSON_GetArraySize(s) == 1, "expected 1 soil item");
    cJSON *item = cJSON_GetArrayItem(s, 0);
    cJSON *p = cJSON_GetObjectItem(item, "p");
    ASSERT(p != NULL && strcmp(p->valuestring, "?") == 0, "null pin should become '?'");

    cJSON_Delete(root);
    PASS();
}

/* ── Test 8: Ri clamping ──────────────────────────────────────────────────── */
static void test_payload_ri_clamping(void) {
    TEST("ri clamping [1, 120]");

    edge_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.ts = 1700000000.0;
    frame.ambient_valid = 0x0F;

    /* Too low */
    frame.report_interval_minutes = 0;
    char buf[PAYLOAD_BUFFER_SIZE];
    payload_build(&frame, buf, sizeof(buf));
    cJSON *root = cJSON_Parse(buf);
    cJSON *ri = cJSON_GetObjectItem(root, "ri");
    ASSERT(ri->valueint == MOLE_REPORT_INTERVAL_DEFAULT,
           "ri should default to MOLE_REPORT_INTERVAL_DEFAULT when < 1");
    cJSON_Delete(root);

    /* Too high */
    frame.report_interval_minutes = 999;
    payload_build(&frame, buf, sizeof(buf));
    root = cJSON_Parse(buf);
    ri = cJSON_GetObjectItem(root, "ri");
    ASSERT(ri->valueint == 120, "ri should cap at 120 when > 120");
    cJSON_Delete(root);

    PASS();
}

/* ── Main ─────────────────────────────────────────────────────────────────── */
int main(void) {
    printf("\n=== payload_builder host tests ===\n\n");

    test_payload_basic();
    test_payload_partial();
    test_payload_no_soil();
    test_payload_overflow();
    test_payload_dg_bitmask();
    test_payload_max_soil();
    test_payload_null_pin();
    test_payload_ri_clamping();

    printf("\n=== Results: %d passed, %d failed ===\n\n",
           tests_passed, tests_failed);
    return tests_failed > 0 ? 1 : 0;
}
