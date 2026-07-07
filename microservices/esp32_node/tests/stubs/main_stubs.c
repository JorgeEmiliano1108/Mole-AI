/*
 * Stubs for extern functions called by state_machine.c.
 * These are linked only for host-side behavioral tests.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include "nvs.h"

void ble_provisioning_start(void) { fprintf(stderr, "stub: ble_provisioning_start\n"); }
void start_captive_portal(void)   { fprintf(stderr, "stub: start_captive_portal (would restart)\n"); exit(0); }
void wifi_init_sta(void)          { fprintf(stderr, "stub: wifi_init_sta\n"); }
esp_err_t mole_ntp_init(void)          { fprintf(stderr, "stub: mole_ntp_init\n"); return ESP_OK; }
esp_err_t mole_ntp_wait_sync(uint32_t t) { (void)t; fprintf(stderr, "stub: ntp_wait_sync\n"); return ESP_OK; }
void sensor_init_all(void)        { fprintf(stderr, "stub: sensor_init_all\n"); }
int  sensor_get_degraded_bitmask(void) { return 0; }
void transport_init_and_connect(void)  { fprintf(stderr, "stub: transport_init_and_connect\n"); }
void transport_send_payload(void)      { fprintf(stderr, "stub: transport_send_payload\n"); }
void start_backoff_timer(void)         { fprintf(stderr, "stub: start_backoff_timer\n"); }
void enter_deep_sleep(void)            { fprintf(stderr, "stub: enter_deep_sleep (would sleep)\n"); }

/* SemaphoreHandle_t from main.c */
void *g_provision_sem = NULL;

/* Offline buffer stubs (not exercised by current FSM behavioral tests) */
#include <stdbool.h>
#include "sensor_frame.h"
bool offline_buffer_init(int capacity)         { (void)capacity; return true; }
int  offline_buffer_count(void)                { return 0; }
bool offline_buffer_pop(sensor_frame_t *frame) { (void)frame; return false; }
void transport_send_frame_from_buffer(const sensor_frame_t *frame) { (void)frame; }
