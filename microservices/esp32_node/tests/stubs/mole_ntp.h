#pragma once
#include "nvs.h"
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

esp_err_t mole_ntp_init(void);
esp_err_t mole_ntp_wait_sync(uint32_t timeout_ms);
bool mole_ntp_is_synced(void);
esp_err_t mole_ntp_get_iso8601(char *buf, size_t buf_len);
