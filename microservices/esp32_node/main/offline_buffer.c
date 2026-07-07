#include <stdlib.h>
#include <string.h>
#include "esp_log.h"
#include "offline_buffer.h"

#define OFFLINE_BUF_TAG "OFFBUF"

static sensor_frame_t *s_buf = NULL;
static int s_capacity = 0;
static int s_head = 0;
static int s_count = 0;

bool offline_buffer_init(int capacity)
{
    if (capacity < 1) {
        ESP_LOGE(OFFLINE_BUF_TAG, "Invalid capacity %d", capacity);
        return false;
    }
    offline_buffer_clear();
    s_buf = (sensor_frame_t *)malloc((size_t)capacity * sizeof(sensor_frame_t));
    if (!s_buf) {
        ESP_LOGE(OFFLINE_BUF_TAG, "malloc(%d) failed", capacity);
        s_capacity = 0;
        return false;
    }
    s_capacity = capacity;
    s_head = 0;
    s_count = 0;
    memset(s_buf, 0, (size_t)capacity * sizeof(sensor_frame_t));
    ESP_LOGI(OFFLINE_BUF_TAG, "Buffer init: capacity=%d", capacity);
    return true;
}

bool offline_buffer_push(const sensor_frame_t *frame)
{
    if (!s_buf || !frame) return false;

    if (s_count >= s_capacity) {
        s_buf[s_head] = *frame;
        s_head = (s_head + 1) % s_capacity;
        ESP_LOGW(OFFLINE_BUF_TAG, "Buffer full — dropped oldest");
        return true;
    }

    int idx = (s_head + s_count) % s_capacity;
    s_buf[idx] = *frame;
    s_count++;
    return true;
}

bool offline_buffer_pop(sensor_frame_t *frame)
{
    if (!s_buf || !frame || s_count <= 0) return false;

    *frame = s_buf[s_head];
    s_head = (s_head + 1) % s_capacity;
    s_count--;
    return true;
}

int offline_buffer_count(void)
{
    return s_count;
}

void offline_buffer_clear(void)
{
    if (s_buf) {
        free(s_buf);
        s_buf = NULL;
    }
    s_capacity = 0;
    s_head = 0;
    s_count = 0;
}

bool offline_buffer_is_full(void)
{
    return s_count >= s_capacity;
}
