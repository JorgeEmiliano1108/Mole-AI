#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "offline_buffer.h"

static int s_pass = 0, s_fail = 0;

static void test_push_pop_fifo(void)
{
    offline_buffer_init(5);
    for (int i = 0; i < 5; i++) {
        sensor_frame_t f;
        memset(&f, 0, sizeof(f));
        f.ts = (double)(1000 + i);
        offline_buffer_push(&f);
    }
    if (offline_buffer_count() != 5) {
        printf("  FAIL: expected count=5, got %d\n", offline_buffer_count());
        s_fail++; return;
    }
    for (int i = 0; i < 5; i++) {
        sensor_frame_t f;
        if (!offline_buffer_pop(&f)) {
            printf("  FAIL: pop failed at index %d\n", i);
            s_fail++; return;
        }
        if (f.ts != (double)(1000 + i)) {
            printf("  FAIL: pop ts=%.0f, expected %.0f\n", f.ts, (double)(1000 + i));
            s_fail++; return;
        }
    }
    if (offline_buffer_count() != 0) {
        printf("  FAIL: expected count=0 after draining, got %d\n", offline_buffer_count());
        s_fail++; return;
    }
    printf("  PASS\n");
    s_pass++;
    offline_buffer_clear();
}

static void test_drop_oldest(void)
{
    offline_buffer_init(3);
    sensor_frame_t f;
    memset(&f, 0, sizeof(f));

    f.ts = 1; offline_buffer_push(&f);
    f.ts = 2; offline_buffer_push(&f);
    f.ts = 3; offline_buffer_push(&f);
    /* now full — push #4 drops oldest (#1) */
    f.ts = 4; offline_buffer_push(&f);

    if (offline_buffer_count() != 3) {
        printf("  FAIL: expected count=3, got %d\n", offline_buffer_count());
        s_fail++; offline_buffer_clear(); return;
    }

    offline_buffer_pop(&f);
    if (f.ts != 2) {
        printf("  FAIL: expected ts=2 (oldest dropped), got %.0f\n", f.ts);
        s_fail++; offline_buffer_clear(); return;
    }
    printf("  PASS\n");
    s_pass++;
    offline_buffer_clear();
}

static void test_empty_pop(void)
{
    offline_buffer_init(3);
    sensor_frame_t f;
    if (offline_buffer_pop(&f)) {
        printf("  FAIL: pop on empty buffer returned true\n");
        s_fail++; offline_buffer_clear(); return;
    }
    printf("  PASS\n");
    s_pass++;
    offline_buffer_clear();
}

static void test_full_flag(void)
{
    offline_buffer_init(3);
    sensor_frame_t f;
    memset(&f, 0, sizeof(f));

    if (offline_buffer_is_full()) {
        printf("  FAIL: is_full on empty buffer\n");
        s_fail++; offline_buffer_clear(); return;
    }

    offline_buffer_push(&f);
    offline_buffer_push(&f);
    offline_buffer_push(&f);
    if (!offline_buffer_is_full()) {
        printf("  FAIL: is_full false at capacity\n");
        s_fail++; offline_buffer_clear(); return;
    }

    offline_buffer_pop(&f);
    if (offline_buffer_is_full()) {
        printf("  FAIL: is_full true after pop\n");
        s_fail++; offline_buffer_clear(); return;
    }
    printf("  PASS\n");
    s_pass++;
    offline_buffer_clear();
}

static void test_clear(void)
{
    offline_buffer_init(5);
    sensor_frame_t f;
    memset(&f, 0, sizeof(f));
    for (int i = 0; i < 5; i++) offline_buffer_push(&f);
    offline_buffer_clear();
    if (offline_buffer_count() != 0) {
        printf("  FAIL: count=%d after clear\n", offline_buffer_count());
        s_fail++; return;
    }
    printf("  PASS\n");
    s_pass++;
}

static void test_capacity_boundary(void)
{
    offline_buffer_init(30);
    sensor_frame_t f;
    memset(&f, 0, sizeof(f));
    for (int i = 0; i < 31; i++) {
        f.ts = (double)i;
        offline_buffer_push(&f);
    }
    int cnt = offline_buffer_count();
    if (cnt != 30) {
        printf("  FAIL: count=%d after 31 pushes (expected 30)\n", cnt);
        s_fail++; offline_buffer_clear(); return;
    }
    /* oldest (ts=0) should have been dropped */
    offline_buffer_pop(&f);
    if (f.ts != 1) {
        printf("  FAIL: oldest ts=%.0f after overflow (expected 1)\n", f.ts);
        s_fail++; offline_buffer_clear(); return;
    }
    printf("  PASS\n");
    s_pass++;
    offline_buffer_clear();
}

int main(void)
{
    printf("=== offline_buffer tests ===\n\n");
    printf("  TEST: push/pop FIFO ... ");     test_push_pop_fifo();
    printf("  TEST: drop oldest ... ");        test_drop_oldest();
    printf("  TEST: empty pop ... ");          test_empty_pop();
    printf("  TEST: is_full flag ... ");       test_full_flag();
    printf("  TEST: clear ... ");              test_clear();
    printf("  TEST: capacity boundary ... ");  test_capacity_boundary();
    printf("\n=== Results: %d passed, %d failed ===\n", s_pass, s_fail);
    return s_fail > 0 ? 1 : 0;
}
