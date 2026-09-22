/*
 * Host-side unit tests for fee2_frame (FEE2 fixed-point encoder, spec §2).
 * Compile: gcc -I../main/include test_fee2_frame.c ../main/fee2_frame.c \
 *              -lm -o test_fee2_frame.elf
 * Cross-validated byte-for-byte with mobile/test/ble_telemetry_test.dart.
 */
#include <stdio.h>
#include <string.h>
#include "mole_config.h"
#include "edge_frame.h"
#include "fee2_frame.h"

static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) do { printf("  TEST: %s ... ", name); } while(0)
#define PASS() do { printf("PASS\n"); tests_passed++; } while(0)
#define FAIL(msg) do { printf("FAIL: %s\n", msg); tests_failed++; } while(0)
#define ASSERT(cond, msg) do { \
    if (!(cond)) { FAIL(msg); return; } \
} while(0)

/* ── Test 1: Golden vector (19 B, fits single MTU-23 notification) ────────── */
static void test_fee2_golden(void) {
    TEST("golden vector 19B");

    edge_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.ts = 1699123456.0;
    frame.report_interval_minutes = 5;
    frame.ambient_valid = 0x0F;
    frame.ambient.t = 28.4f;
    frame.ambient.h = 65.2f;
    frame.ambient.l = 410.0f;
    frame.ambient.u = 5.5f;
    frame.soil[0].pin = "32";
    frame.soil[0].adc_raw = 2847;
    frame.soil[1].pin = "33";
    frame.soil[1].adc_raw = 3012;
    frame.soil_count = 2;

    /* ts=1699123456 t=2840 h=6520 l=410 u=550 ch4/adc2847 ch5/adc3012 */
    static const uint8_t golden[] = {
        0x00, 0x91, 0x46, 0x65, 0x05, 0x0F, 0x18, 0x0B, 0x78, 0x19,
        0x9A, 0x01, 0x26, 0x02, 0x02, 0x4B, 0x1F, 0x5B, 0xC4
    };

    uint8_t out[FEE2_MAX_FRAME_LEN];
    int len = fee2_encode(&frame, out, sizeof(out));
    ASSERT(len == 19, "golden length != 19");
    ASSERT(len <= 20, "golden must fit single MTU-23 payload");
    ASSERT(memcmp(out, golden, sizeof(golden)) == 0, "golden bytes mismatch");
    PASS();
}

/* ── Test 2: Negative temperature (i16 two's complement) ─────────────────── */
static void test_fee2_negative_temp(void) {
    TEST("negative temp i16");

    edge_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.ts = 1700000000.0;
    frame.report_interval_minutes = 5;
    frame.ambient_valid = AMBIENT_VALID_TEMP_BIT;
    frame.ambient.t = -5.25f;
    frame.soil_count = 0;

    uint8_t out[FEE2_MAX_FRAME_LEN];
    int len = fee2_encode(&frame, out, sizeof(out));
    ASSERT(len == 9, "length != 9 (6 hdr + 2 + 1 count)");
    /* -525 = 0xFDF3 LE */
    ASSERT(out[6] == 0xF3 && out[7] == 0xFD, "i16 LE mismatch for -5.25C");
    ASSERT(out[8] == 0, "soil_count != 0");
    PASS();
}

/* ── Test 3: Invalid GPIO skipped, count patched ──────────────────────────── */
static void test_fee2_invalid_pin(void) {
    TEST("invalid pin skipped");

    edge_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    frame.ts = 1700000000.0;
    frame.report_interval_minutes = 5;
    frame.ambient_valid = 0;
    frame.soil[0].pin = "4";      /* ADC2 — conflicts with WiFi, skip */
    frame.soil[0].adc_raw = 2000;
    frame.soil[1].pin = "34";     /* ADC1 ch6 — keep */
    frame.soil[1].adc_raw = 4095; /* clamp top */
    frame.soil[2].pin = NULL;     /* NULL — skip */
    frame.soil[2].adc_raw = 100;
    frame.soil_count = 3;

    uint8_t out[FEE2_MAX_FRAME_LEN];
    int len = fee2_encode(&frame, out, sizeof(out));
    ASSERT(len == 9, "length != 9 (6 hdr + 1 count + 2 kept)");
    ASSERT(out[6] == 1, "soil_count != 1 after skips");
    /* ch6 + adc 4095 (0xFFF): b0 = 0x6F, b1 = 0xFF */
    ASSERT(out[7] == 0x6F && out[8] == 0xFF, "packed probe mismatch");
    PASS();
}

/* ── Test 4: Guards (NULL, short buffer, ri clamp, count clamp) ───────────── */
static void test_fee2_guards(void) {
    TEST("guards + clamping");

    edge_frame_t frame;
    memset(&frame, 0, sizeof(frame));
    uint8_t out[FEE2_MAX_FRAME_LEN];

    ASSERT(fee2_encode(NULL, out, sizeof(out)) == -1, "NULL frame accepted");
    ASSERT(fee2_encode(&frame, NULL, sizeof(out)) == -1, "NULL out accepted");
    frame.ts = 1.0;
    ASSERT(fee2_encode(&frame, out, 6) == -1, "short buffer accepted");

    /* ri < 1 → default 5; ri > 120 → 120 */
    frame.report_interval_minutes = 0;
    ASSERT(fee2_encode(&frame, out, sizeof(out)) == 7, "empty frame != 7B");
    ASSERT(out[4] == MOLE_REPORT_INTERVAL_DEFAULT, "ri default != 5");
    frame.report_interval_minutes = 999;
    fee2_encode(&frame, out, sizeof(out));
    ASSERT(out[4] == 120, "ri cap != 120");

    /* soil_count > max → clamped to 8 */
    frame.soil_count = 99;
    int len = fee2_encode(&frame, out, sizeof(out));
    ASSERT(len == 7 + 0, "clamped count changed empty length");
    ASSERT(out[6] == 0, "count != 0 (all pins invalid/empty)");
    PASS();
}

/* ── Main ─────────────────────────────────────────────────────────────────── */
int main(void) {
    printf("\n=== fee2_frame host tests ===\n\n");

    test_fee2_golden();
    test_fee2_negative_temp();
    test_fee2_invalid_pin();
    test_fee2_guards();

    printf("\n=== Results: %d passed, %d failed ===\n\n",
           tests_passed, tests_failed);
    return tests_failed > 0 ? 1 : 0;
}
