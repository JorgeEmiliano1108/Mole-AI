#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SENSOR_FRAME_MAX_SOIL_PINS   8

typedef struct {
    double  ts;
    int     report_interval_minutes;
    struct {
        float t;
        float h;
        float l;
        float u;
    } ambient;
    int ambient_valid;
    struct {
        char    pin[8];
        int     adc_raw;
    } soil[SENSOR_FRAME_MAX_SOIL_PINS];
    int soil_count;
} sensor_frame_t;

#ifdef __cplusplus
}
#endif
