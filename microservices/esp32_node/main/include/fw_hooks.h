/*
 * fw_hooks.h — Firmware action hooks (implementadas en main.c)
 *
 * El FSM (state_machine.c) orquesta la secuencia de arranque invocando
 * estas primitivas de plataforma. Se declaran aquí (y por tanto se
 * exportan desde main.c) para que el plano lógico desacople del plano
 * hardware, el mismo contrato que usan los stubs en tests/.
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "sensor_frame.h"

#ifdef __cplusplus
extern "C" {
#endif

/* SECTION NVS: carga token + wifi_ssid; true si credenciales completas y
 * pobla s_device_token (usado por transport_init_and_connect). */
bool nvs_load_token(void);

/* SECTION Provisioning: captive portal (bloquea hasta completar) */
void start_captive_portal(void);

/* SECTION WiFi STA: no bloquea, postea eventos a la cola FSM */
void wifi_init_sta(void);

/* SECTION Transport: init + primera conexión, no bloquea */
void transport_init_and_connect(void);

/* SECTION Sensores: inicializa todos los canales, no bloquea */
void sensor_init_all(void);

/* Devuelve el bitmask de sensores degradados (0 = todos OK) */
int sensor_get_degraded_bitmask(void);

/* SECTION Telemetría: publica la muestra actual al backend (no bloquea) */
void transport_send_payload(void);

/* SECTION Backoff: arranca el temporizador de reconexión (no bloquea) */
void start_backoff_timer(void);

/* SECTION Deep Sleep: apaga y entra en deep sleep (no retorna) */
void enter_deep_sleep(void);

/* SECTION Drain: envía una trama bufferizada (Store&Forward) */
void transport_send_frame_from_buffer(const sensor_frame_t *frame);

/* SECTION Buffer: muestrea (si hace falta) y guarda la muestra actual en el
 * buffer offline (drop-oldest si está lleno). No bloquea. */
void buffer_current_sample(void);

#ifdef __cplusplus
}
#endif