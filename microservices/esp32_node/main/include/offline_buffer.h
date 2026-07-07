#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "sensor_frame.h"

#ifdef __cplusplus
extern "C" {
#endif

bool offline_buffer_init(int capacity);
bool offline_buffer_push(const sensor_frame_t *frame);
bool offline_buffer_pop(sensor_frame_t *frame);
int  offline_buffer_count(void);
void offline_buffer_clear(void);
bool offline_buffer_is_full(void);

#ifdef __cplusplus
}
#endif
