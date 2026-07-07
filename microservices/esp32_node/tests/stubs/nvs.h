#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>

typedef int nvs_handle_t;
#define NVS_READONLY  0
#define NVS_READWRITE 1

/* In-memory NVS store for stubs */
#define NVS_STUB_KEY_MAX 8
#define NVS_STUB_SIZE    64

extern uint8_t nvs_stub_data[256]; /* flat key-value store */

typedef enum { ESP_OK = 0, ESP_FAIL = 1, ESP_ERR_NVS_NOT_FOUND = 2 } esp_err_t;

static inline esp_err_t nvs_open(const char *ns, int open_mode, nvs_handle_t *h) {
    (void)ns; (void)open_mode; *h = 1; return ESP_OK;
}
static inline void nvs_close(nvs_handle_t h) { (void)h; }
static inline esp_err_t nvs_commit(nvs_handle_t h) { (void)h; return ESP_OK; }

static inline esp_err_t nvs_get_u8(nvs_handle_t h, const char *key, uint8_t *val) {
    (void)h; (void)key; *val = 0; return ESP_ERR_NVS_NOT_FOUND;
}
static inline esp_err_t nvs_set_u8(nvs_handle_t h, const char *key, uint8_t val) {
    (void)h; (void)key; (void)val; return ESP_OK;
}
static inline esp_err_t nvs_get_i32(nvs_handle_t h, const char *key, int32_t *val) {
    (void)h; (void)key; *val = 0; return ESP_ERR_NVS_NOT_FOUND;
}
static inline esp_err_t nvs_set_i32(nvs_handle_t h, const char *key, int32_t val) {
    (void)h; (void)key; (void)val; return ESP_OK;
}
static inline esp_err_t nvs_get_str(nvs_handle_t h, const char *key, char *buf, size_t *len) {
    (void)h; (void)key; (void)buf; *len = 0; return ESP_ERR_NVS_NOT_FOUND;
}
static inline esp_err_t nvs_set_str(nvs_handle_t h, const char *key, const char *val) {
    (void)h; (void)key; (void)val; return ESP_OK;
}
