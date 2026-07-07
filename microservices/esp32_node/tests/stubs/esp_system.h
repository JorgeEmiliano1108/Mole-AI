#pragma once
#include <stdlib.h>
#define esp_restart() do { fprintf(stderr, "esp_restart called\n"); exit(0); } while(0)
#define esp_random() rand()
